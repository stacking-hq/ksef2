"""Profile configuration shared by SDK authentication clients."""

import os
import tomllib
from collections.abc import Mapping
from enum import StrEnum
import json
from pathlib import Path
import re
from typing import Self

from cryptography.x509 import Certificate
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from ksef2.config import Environment
from ksef2.core import exceptions
from ksef2.core.xades import (
    XAdESPrivateKey,
    load_certificate_and_key_from_p12,
    load_certificate_from_pem,
    load_private_key_from_pem,
)
from ksef2.domain.models.auth import ContextIdentifierType, ContextIdentifierTypeEnum

CONFIG_ENV_VAR = "KSEF2_CONFIG"
PROFILE_ENV_VAR = "KSEF2_PROFILE"
CONFIG_FILE_MODE = 0o600
PROFILE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

_ENVIRONMENT_TO_PROFILE = {
    Environment.PRODUCTION: "production",
    Environment.DEMO: "demo",
    Environment.TEST: "test",
}


class ProfileEnvironment(StrEnum):
    PRODUCTION = "production"
    DEMO = "demo"
    TEST = "test"


class ProfileAuthType(StrEnum):
    TOKEN = "token"
    TEST_CERTIFICATE = "test_certificate"
    XADES_PEM = "xades_pem"
    XADES_P12 = "xades_p12"


class ProfileAuthConfig(BaseModel):
    type: ProfileAuthType
    token_env: str | None = Field(
        default=None, description="Environment variable containing a KSeF token."
    )
    context_type: ContextIdentifierTypeEnum | ContextIdentifierType | None = Field(
        default=None, description="Token-auth context type."
    )
    cert: str | Path | None = Field(
        default=None, description="PEM certificate path for XAdES authentication."
    )
    key: str | Path | None = Field(
        default=None, description="PEM private key path for XAdES authentication."
    )
    key_password_env: str | None = Field(
        default=None,
        description="Environment variable containing an encrypted PEM key password.",
    )
    p12: str | Path | None = Field(
        default=None, description="PKCS#12/PFX archive path for XAdES authentication."
    )
    p12_password_env: str | None = Field(
        default=None,
        description="Environment variable containing a PKCS#12/PFX archive password.",
    )

    @field_validator("cert", "key", "p12", mode="after")
    @classmethod
    def _expand_path(cls, value: str | Path | None) -> Path | None:
        return Path(value).expanduser() if value else None

    @model_validator(mode="after")
    def _validate_auth_fields(self) -> Self:
        if self.type is ProfileAuthType.TOKEN and not self.token_env:
            raise ValueError("Token profiles require auth.token_env.")
        if self.type is ProfileAuthType.XADES_PEM and (
            self.cert is None or self.key is None
        ):
            raise ValueError("PEM XAdES profiles require auth.cert and auth.key.")
        if self.type is ProfileAuthType.XADES_P12 and self.p12 is None:
            raise ValueError("PKCS#12/PFX profiles require auth.p12.")
        return self


class TokenProfileAuth(ProfileAuthConfig):
    type: ProfileAuthType = ProfileAuthType.TOKEN


class TestCertificateProfileAuth(ProfileAuthConfig):
    type: ProfileAuthType = ProfileAuthType.TEST_CERTIFICATE


class XadesPemProfileAuth(ProfileAuthConfig):
    type: ProfileAuthType = ProfileAuthType.XADES_PEM


class XadesP12ProfileAuth(ProfileAuthConfig):
    type: ProfileAuthType = ProfileAuthType.XADES_P12


class ProfileConfig(BaseModel):
    environment: ProfileEnvironment | Environment
    nip: str
    auth: ProfileAuthConfig
    poll_interval: float | None = Field(
        default=None, ge=0.1, description="Authentication polling interval."
    )
    max_poll_attempts: int | None = Field(
        default=None, ge=1, description="Authentication polling attempts."
    )

    @field_validator("environment", mode="before")
    @classmethod
    def _normalize_environment(cls, value: object) -> object:
        if isinstance(value, Environment):
            return _ENVIRONMENT_TO_PROFILE[value]
        return value

    @property
    def sdk_environment(self) -> Environment:
        if isinstance(self.environment, Environment):
            return self.environment
        return _profile_environment_to_sdk(self.environment)


class CliProfileConfig(BaseModel):
    active_profile: str | None = None
    profiles: dict[str, ProfileConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_active_profile(self) -> Self:
        if self.active_profile is not None and self.active_profile not in self.profiles:
            raise ValueError(f"Active profile {self.active_profile!r} is not defined.")
        return self


Profile = ProfileConfig


class ProfileStore:
    """Read and write local profiles compatible with ``ksef2-cli``."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = _resolve_profile_config_path(path)

    @classmethod
    def default(cls) -> Self:
        return cls()

    def load(self) -> CliProfileConfig:
        return load_profile_config(self.path)

    def save(
        self,
        name: str,
        profile: ProfileConfig,
        *,
        activate: bool = True,
        overwrite: bool = False,
    ) -> ProfileConfig:
        config = self.load()
        if name in config.profiles and not overwrite:
            raise exceptions.KSeFValidationError(
                f"ksef2-cli profile {name!r} already exists.",
                config_path=str(self.path),
                profile_name=name,
            )

        config.profiles[name] = profile
        if activate:
            config.active_profile = name
        write_profile_config(self.path, config)
        return profile

    def get(self, name: str) -> ProfileConfig:
        config = self.load()
        profile = config.profiles.get(name)
        if profile is None:
            raise exceptions.KSeFValidationError(
                f"ksef2-cli profile {name!r} is not defined in {self.path}.",
                config_path=str(self.path),
                profile_name=name,
            )
        return profile

    def list(self) -> dict[str, ProfileConfig]:
        return dict(self.load().profiles)

    def current(self) -> tuple[str, ProfileConfig] | None:
        config = self.load()
        if config.active_profile is None:
            return None
        return config.active_profile, config.profiles[config.active_profile]

    def use(self, name: str) -> ProfileConfig:
        config = self.load()
        profile = config.profiles.get(name)
        if profile is None:
            raise exceptions.KSeFValidationError(
                f"ksef2-cli profile {name!r} is not defined in {self.path}.",
                config_path=str(self.path),
                profile_name=name,
            )

        config.active_profile = name
        write_profile_config(self.path, config)
        return profile

    def delete(self, name: str) -> ProfileConfig:
        config = self.load()
        profile = config.profiles.pop(name, None)
        if profile is None:
            raise exceptions.KSeFValidationError(
                f"ksef2-cli profile {name!r} is not defined in {self.path}.",
                config_path=str(self.path),
                profile_name=name,
            )

        if config.active_profile == name:
            config.active_profile = None
        write_profile_config(self.path, config)
        return profile


def default_profile_config_path(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    override = env.get(CONFIG_ENV_VAR)
    if override:
        return Path(override).expanduser()
    config_home = Path(env.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home.expanduser() / "ksef2-cli" / "config.toml"


def load_profile_config(path: str | Path | None = None) -> CliProfileConfig:
    config_path = _resolve_profile_config_path(path)
    if not config_path.exists():
        return CliProfileConfig()

    try:
        payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
        return CliProfileConfig.model_validate(payload)
    except tomllib.TOMLDecodeError as exc:
        raise exceptions.KSeFValidationError(
            f"Invalid ksef2-cli profile config at {config_path}: {exc}",
            config_path=str(config_path),
        ) from exc
    except ValidationError as exc:
        raise exceptions.KSeFValidationError(
            f"Invalid ksef2-cli profile config at {config_path}: {exc}",
            config_path=str(config_path),
        ) from exc


def write_profile_config(path: str | Path, config: CliProfileConfig) -> None:
    config_path = Path(path).expanduser()
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        _ = config_path.write_text(render_profile_config(config), encoding="utf-8")
        _ = config_path.chmod(CONFIG_FILE_MODE)
    except OSError as exc:
        raise exceptions.KSeFValidationError(
            f"Failed to write ksef2-cli profile config at {config_path}: {exc}",
            config_path=str(config_path),
        ) from exc


def render_profile_config(config: CliProfileConfig) -> str:
    lines = [
        "# ksef2-cli local profiles",
        "# CLI options override the selected profile for one invocation.",
        "# Store token and password secrets in environment variables.",
    ]
    if config.active_profile is not None:
        lines.append(f"active_profile = {_toml_string(config.active_profile)}")

    for name, profile in config.profiles.items():
        lines.extend(
            [
                "",
                f"[profiles.{_toml_key(name)}]",
                f"environment = {_toml_string(_profile_environment_value(profile.environment))}",
                f"nip = {_toml_string(profile.nip)}",
            ]
        )
        if profile.poll_interval is not None:
            lines.append(f"poll_interval = {_toml_number(profile.poll_interval)}")
        if profile.max_poll_attempts is not None:
            lines.append(f"max_poll_attempts = {profile.max_poll_attempts}")

        auth = profile.auth
        lines.extend(
            [
                "",
                f"[profiles.{_toml_key(name)}.auth]",
                f"type = {_toml_string(auth.type.value)}",
            ]
        )
        if auth.token_env is not None:
            lines.append(f"token_env = {_toml_string(auth.token_env)}")
        if auth.context_type is not None:
            lines.append(f"context_type = {_toml_string(profile_context_type(auth))}")
        if auth.cert is not None:
            lines.append(f"cert = {_toml_string(str(auth.cert))}")
        if auth.key is not None:
            lines.append(f"key = {_toml_string(str(auth.key))}")
        if auth.key_password_env is not None:
            lines.append(f"key_password_env = {_toml_string(auth.key_password_env)}")
        if auth.p12 is not None:
            lines.append(f"p12 = {_toml_string(str(auth.p12))}")
        if auth.p12_password_env is not None:
            lines.append(f"p12_password_env = {_toml_string(auth.p12_password_env)}")

    return "\n".join(lines) + "\n"


def load_cli_profile(
    name: str | None = None,
    *,
    config_path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> tuple[str, ProfileConfig]:
    env = os.environ if environ is None else environ
    resolved_config_path = _resolve_profile_config_path(config_path, environ=env)
    config = load_profile_config(resolved_config_path)
    selected_name = name or env.get(PROFILE_ENV_VAR) or config.active_profile

    if selected_name is None:
        raise exceptions.KSeFValidationError(
            "No ksef2-cli profile selected. Pass a profile name, set KSEF2_PROFILE, "
            f"or configure active_profile in {resolved_config_path}.",
            config_path=str(resolved_config_path),
        )

    profile = config.profiles.get(selected_name)
    if profile is None:
        raise exceptions.KSeFValidationError(
            f"ksef2-cli profile {selected_name!r} is not defined in "
            f"{resolved_config_path}.",
            config_path=str(resolved_config_path),
            profile_name=selected_name,
        )

    return selected_name, profile


def resolve_profile_secret(
    envvar: str | None,
    *,
    label: str,
    profile_name: str,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    if envvar is None:
        return None

    env = os.environ if environ is None else environ
    value = env.get(envvar)
    if value is None:
        raise exceptions.KSeFValidationError(
            f"{label} environment variable {envvar} is not set for "
            f"ksef2-cli profile {profile_name!r}.",
            profile_name=profile_name,
            envvar=envvar,
        )
    return value


def load_profile_pem_credentials(
    profile: ProfileConfig,
    *,
    profile_name: str,
) -> tuple[Certificate, XAdESPrivateKey]:
    auth = profile.auth
    if auth.cert is None or auth.key is None:
        raise exceptions.KSeFValidationError(
            f"ksef2-cli profile {profile_name!r} requires auth.cert and auth.key.",
            profile_name=profile_name,
        )

    password = resolve_profile_secret(
        auth.key_password_env,
        label="PEM private key password",
        profile_name=profile_name,
    )
    try:
        return (
            load_certificate_from_pem(auth.cert),
            load_private_key_from_pem(
                auth.key,
                password=password.encode("utf-8") if password else None,
            ),
        )
    except (OSError, TypeError, ValueError) as exc:
        raise exceptions.KSeFValidationError(
            f"Failed to load PEM credentials for ksef2-cli profile "
            f"{profile_name!r}: {exc}",
            profile_name=profile_name,
            cert_path=str(auth.cert),
            key_path=str(auth.key),
        ) from exc


def load_profile_p12_credentials(
    profile: ProfileConfig,
    *,
    profile_name: str,
) -> tuple[Certificate, XAdESPrivateKey]:
    auth = profile.auth
    if auth.p12 is None:
        raise exceptions.KSeFValidationError(
            f"ksef2-cli profile {profile_name!r} requires auth.p12.",
            profile_name=profile_name,
        )

    password = resolve_profile_secret(
        auth.p12_password_env,
        label="PKCS#12/PFX password",
        profile_name=profile_name,
    )
    try:
        return load_certificate_and_key_from_p12(
            auth.p12,
            password=password.encode("utf-8") if password else None,
        )
    except (OSError, TypeError, ValueError) as exc:
        raise exceptions.KSeFValidationError(
            f"Failed to load PKCS#12/PFX credentials for ksef2-cli profile "
            f"{profile_name!r}: {exc}",
            profile_name=profile_name,
            p12_path=str(auth.p12),
        ) from exc


def _resolve_profile_config_path(
    path: str | Path | None,
    *,
    environ: Mapping[str, str] | None = None,
) -> Path:
    if path is not None:
        return Path(path).expanduser()
    return default_profile_config_path(environ)


def profile_context_type(auth: ProfileAuthConfig) -> ContextIdentifierType:
    context_type = auth.context_type
    if isinstance(context_type, ContextIdentifierTypeEnum):
        return context_type.value
    return context_type or "nip"


def _profile_environment_to_sdk(environment: ProfileEnvironment) -> Environment:
    if environment is ProfileEnvironment.PRODUCTION:
        return Environment.PRODUCTION
    if environment is ProfileEnvironment.DEMO:
        return Environment.DEMO
    return Environment.TEST


def _profile_environment_value(environment: ProfileEnvironment | Environment) -> str:
    if isinstance(environment, Environment):
        return _ENVIRONMENT_TO_PROFILE[environment]
    return environment.value


def _toml_key(value: str) -> str:
    if PROFILE_NAME_PATTERN.fullmatch(value):
        return value
    return _toml_string(value)


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _toml_number(value: float) -> str:
    return str(value)
