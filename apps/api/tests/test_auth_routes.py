from app.main import app


def test_auth_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
