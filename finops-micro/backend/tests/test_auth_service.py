from finops_api.services.auth_service import AuthService


def test_allowed_email_domain_accepts_algar() -> None:
    AuthService.ensure_allowed_email_domain("usuario@algar.com.br")
    AuthService.ensure_allowed_email_domain("usuario@algartelecom.com.br")


def test_allowed_email_domain_rejects_external() -> None:
    try:
        AuthService.ensure_allowed_email_domain("usuario@gmail.com")
    except ValueError as exc:
        assert "domínio Algar" in str(exc)
    else:
        raise AssertionError("Era esperado rejeitar domínio externo")


def test_password_hash_roundtrip() -> None:
    encoded = AuthService.hash_password("SenhaForte123")

    assert AuthService.verify_password("SenhaForte123", encoded) is True
    assert AuthService.verify_password("SenhaErrada", encoded) is False
