import stat
from pathlib import Path

import pytest

from ksef2.clients.profiles import (
    CONFIG_ENV_VAR,
    PROFILE_ENV_VAR,
    CliProfileConfig,
    Profile,
    ProfileAuthConfig,
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

    xdg_home = tmp_path / "xdg"
    assert default_profile_config_path({"XDG_CONFIG_HOME": str(xdg_home)}) == (
        xdg_home / "ksef2" / "config.toml"
    )

    legacy_path = xdg_home / "ksef2-cli" / "config.toml"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text("", encoding="utf-8")
    assert default_profile_config_path({"XDG_CONFIG_HOME": str(xdg_home)}) == (
        legacy_path
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


_LEGACY_PROFILE = """
[profiles.legacy]
environment = "test"
nip = "1111111111"
{extra}

[profiles.legacy.auth]
type = "test_certificate"
"""


def _load_legacy(tmp_path: Path, extra: str) -> Profile:
    config_path = tmp_path / "config.toml"
    config_path.write_text(_LEGACY_PROFILE.format(extra=extra))
    return load_profile_config(config_path).profiles["legacy"]


@pytest.mark.parametrize(
    ("extra", "attempts", "interval"),
    [
        ("auth_timeout = 180.0", 180, None),
        ("auth_timeout = 12", 12, None),
        ("auth_timeout = 0.5", 1, None),
        ("auth_timeout = 10.0\npoll_interval = 4.0", 3, 4.0),
    ],
)
def test_legacy_auth_timeout_maps_to_poll_settings_with_warning(
    tmp_path: Path, extra: str, attempts: int, interval: float | None
) -> None:
    with pytest.deprecated_call(match="`auth_timeout` profile key is deprecated"):
        profile = _load_legacy(tmp_path, extra)

    assert profile.max_poll_attempts == attempts
    assert profile.poll_interval == interval
    # Same formula with_profile() uses to derive its timeout.
    assert attempts * (interval or 1.0) >= float(extra.split()[2].split("\n")[0])


def test_legacy_auth_timeout_does_not_override_explicit_max_poll_attempts(
    tmp_path: Path,
) -> None:
    with pytest.deprecated_call(match="auth_timeout"):
        profile = _load_legacy(tmp_path, "auth_timeout = 180.0\nmax_poll_attempts = 7")

    assert profile.max_poll_attempts == 7


def test_other_unknown_profile_keys_stay_ignored_without_warning(
    tmp_path: Path,
) -> None:
    profile = _load_legacy(tmp_path, 'output = "json"\nverbose = true')

    assert profile.max_poll_attempts is None
    assert not hasattr(profile, "output")


def _profile(
    *,
    cert: str | None = None,
    key: str | None = None,
    p12: str | None = None,
    context_type: str | None = None,
) -> Profile:
    # model_construct skips the auth validators so the loaders' own guards run.
    return Profile.model_construct(
        environment=Environment.TEST,
        nip="1111111111",
        auth=ProfileAuthConfig.model_construct(
            type=ProfileAuthType.XADES_PEM,
            cert=cert,
            key=key,
            p12=p12,
            context_type=context_type,
        ),
    )


def test_resolve_profile_secret_reads_the_named_variable() -> None:
    from ksef2.clients.profiles import resolve_profile_secret

    assert resolve_profile_secret(None, label="x", profile_name="p", environ={}) is None
    assert (
        resolve_profile_secret(
            "PW", label="x", profile_name="p", environ={"PW": "secret"}
        )
        == "secret"
    )
    with pytest.raises(KSeFValidationError, match="PW is not set"):
        resolve_profile_secret("PW", label="Password", profile_name="p", environ={})


def test_pem_credentials_require_cert_and_key_and_wrap_load_errors(tmp_path) -> None:
    from ksef2.clients.profiles import load_profile_pem_credentials

    with pytest.raises(KSeFValidationError, match="requires auth.cert and auth.key"):
        load_profile_pem_credentials(_profile(), profile_name="p")

    bad = tmp_path / "not-a-pem.pem"
    bad.write_text("garbage")
    with pytest.raises(KSeFValidationError, match="Failed to load PEM credentials"):
        load_profile_pem_credentials(
            _profile(cert=str(bad), key=str(bad)), profile_name="p"
        )
    with pytest.raises(KSeFValidationError, match="Failed to load PEM credentials"):
        load_profile_pem_credentials(
            _profile(cert=str(tmp_path / "missing.pem"), key=str(bad)),
            profile_name="p",
        )


def test_p12_credentials_require_a_path_and_wrap_load_errors(tmp_path) -> None:
    from ksef2.clients.profiles import load_profile_p12_credentials

    with pytest.raises(KSeFValidationError, match="requires auth.p12"):
        load_profile_p12_credentials(_profile(), profile_name="p")

    bad = tmp_path / "bad.p12"
    bad.write_bytes(b"not a pkcs12 archive")
    with pytest.raises(KSeFValidationError, match="Failed to load PKCS#12/PFX"):
        load_profile_p12_credentials(_profile(p12=str(bad)), profile_name="p")


def test_profile_context_type_defaults_to_nip() -> None:
    from ksef2.clients.profiles import profile_context_type

    assert profile_context_type(_profile().auth) == "nip"
    assert profile_context_type(_profile(context_type="nip").auth) == "nip"
