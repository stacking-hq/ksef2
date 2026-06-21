import stat
from pathlib import Path

import pytest

from ksef2.clients.profiles import (
    CONFIG_ENV_VAR,
    PROFILE_ENV_VAR,
    CliProfileConfig,
    Profile,
    ProfileAuthType,
    ProfileStore,
    TestCertificateProfileAuth as CertificateProfileAuth,
    TokenProfileAuth,
    XadesP12ProfileAuth,
    XadesPemProfileAuth,
    default_profile_config_path,
    load_cli_profile,
    load_profile_config,
)
from ksef2.config import Environment
from ksef2.core.exceptions import KSeFValidationError


def test_load_cli_profile_uses_active_profile_and_env_override(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
        active_profile = "demo"

        [profiles.demo]
        environment = "test"
        nip = "1111111111"

        [profiles.demo.auth]
        type = "test_certificate"

        [profiles.prod]
        environment = "production"
        nip = "2222222222"

        [profiles.prod.auth]
        type = "token"
        token_env = "KSEF2_PROD_TOKEN"
        context_type = "nip"
        """,
        encoding="utf-8",
    )

    active_name, active_profile = load_cli_profile(config_path=config_path)
    env_name, env_profile = load_cli_profile(
        config_path=config_path,
        environ={PROFILE_ENV_VAR: "prod"},
    )

    assert active_name == "demo"
    assert active_profile.sdk_environment is Environment.TEST
    assert active_profile.auth.type is ProfileAuthType.TEST_CERTIFICATE
    assert env_name == "prod"
    assert env_profile.sdk_environment is Environment.PRODUCTION
    assert env_profile.auth.token_env == "KSEF2_PROD_TOKEN"


def test_load_cli_profile_requires_selected_profile(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("", encoding="utf-8")

    with pytest.raises(KSeFValidationError, match="No ksef2-cli profile selected"):
        load_cli_profile(config_path=config_path, environ={})


def test_load_cli_profile_rejects_unknown_profile(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
        [profiles.demo]
        environment = "test"
        nip = "1111111111"

        [profiles.demo.auth]
        type = "test_certificate"
        """,
        encoding="utf-8",
    )

    with pytest.raises(KSeFValidationError, match="profile 'prod' is not defined"):
        load_cli_profile("prod", config_path=config_path)


def test_load_profile_config_rejects_invalid_profile_shape(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
        [profiles.prod]
        environment = "production"
        nip = "2222222222"

        [profiles.prod.auth]
        type = "token"
        """,
        encoding="utf-8",
    )

    with pytest.raises(KSeFValidationError, match="auth.token_env"):
        load_profile_config(config_path)


def test_missing_profile_config_loads_empty_config(tmp_path) -> None:
    assert load_profile_config(tmp_path / "missing.toml") == CliProfileConfig()


def test_default_profile_config_path_uses_cli_locations(tmp_path) -> None:
    env_path = tmp_path / "from-env.toml"
    assert default_profile_config_path({CONFIG_ENV_VAR: str(env_path)}) == env_path

    assert default_profile_config_path({"XDG_CONFIG_HOME": str(tmp_path / "xdg")}) == (
        tmp_path / "xdg" / "ksef2-cli" / "config.toml"
    )


def test_profile_store_saves_cli_compatible_token_profile(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    store = ProfileStore(config_path)
    profile = Profile(
        environment=Environment.PRODUCTION,
        nip="5261040828",
        auth=TokenProfileAuth(token_env="KSEF2_TOKEN", context_type="nip"),
        poll_interval=1.5,
        max_poll_attempts=12,
    )

    saved = store.save("prod-token", profile)
    loaded_name, loaded_profile = load_cli_profile(config_path=config_path)

    assert saved is profile
    assert loaded_name == "prod-token"
    assert loaded_profile.sdk_environment is Environment.PRODUCTION
    assert loaded_profile.auth.type is ProfileAuthType.TOKEN
    assert loaded_profile.auth.token_env == "KSEF2_TOKEN"
    assert loaded_profile.auth.context_type == "nip"
    assert loaded_profile.poll_interval == 1.5
    assert loaded_profile.max_poll_attempts == 12
    assert stat.S_IMODE(config_path.stat().st_mode) == 0o600
    assert 'active_profile = "prod-token"' in config_path.read_text(encoding="utf-8")


def test_profile_store_supports_all_public_auth_shapes(tmp_path) -> None:
    store = ProfileStore(tmp_path / "config.toml")

    store.save(
        "test-company",
        Profile(
            environment=Environment.TEST,
            nip="5261040828",
            auth=CertificateProfileAuth(),
        ),
    )
    store.save(
        "demo-pem",
        Profile(
            environment=Environment.DEMO,
            nip="5261040828",
            auth=XadesPemProfileAuth(
                cert="company.pem",
                key="company.key",
                key_password_env="KSEF2_KEY_PASSWORD",
            ),
        ),
        activate=False,
    )
    store.save(
        "prod-p12",
        Profile(
            environment=Environment.PRODUCTION,
            nip="5261040828",
            auth=XadesP12ProfileAuth(
                p12="company.p12",
                p12_password_env="KSEF2_P12_PASSWORD",
            ),
        ),
        activate=False,
    )

    profiles = store.list()

    assert profiles["test-company"].auth.type is ProfileAuthType.TEST_CERTIFICATE
    assert isinstance(profiles["demo-pem"].auth.cert, Path)
    assert isinstance(profiles["demo-pem"].auth.key, Path)
    assert isinstance(profiles["prod-p12"].auth.p12, Path)
    assert profiles["demo-pem"].auth.cert.name == "company.pem"
    assert profiles["demo-pem"].auth.key.name == "company.key"
    assert profiles["prod-p12"].auth.p12.name == "company.p12"
    assert store.current() == ("test-company", profiles["test-company"])


def test_profile_store_rejects_existing_profile_without_overwrite(tmp_path) -> None:
    store = ProfileStore(tmp_path / "config.toml")
    profile = Profile(
        environment=Environment.TEST,
        nip="5261040828",
        auth=CertificateProfileAuth(),
    )
    store.save("test-company", profile)

    with pytest.raises(KSeFValidationError, match="already exists"):
        store.save("test-company", profile)

    replacement = Profile(
        environment=Environment.TEST,
        nip="1111111111",
        auth=CertificateProfileAuth(),
    )
    store.save("test-company", replacement, overwrite=True)

    assert store.get("test-company").nip == "1111111111"


def test_profile_store_selects_and_deletes_profiles(tmp_path) -> None:
    store = ProfileStore(tmp_path / "config.toml")
    first = Profile(
        environment=Environment.TEST,
        nip="1111111111",
        auth=CertificateProfileAuth(),
    )
    second = Profile(
        environment=Environment.DEMO,
        nip="2222222222",
        auth=TokenProfileAuth(token_env="KSEF2_DEMO_TOKEN"),
    )
    store.save("first", first)
    store.save("second", second, activate=False)

    selected = store.use("second")
    deleted = store.delete("second")

    assert selected.nip == "2222222222"
    assert deleted.nip == "2222222222"
    assert store.current() is None
    assert list(store.list()) == ["first"]
