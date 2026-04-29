from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD


async def test_register_success(async_client):
    response = await async_client.post(
        "/auth/register",
        json={
            "id": 42,
            "email": "newuser@example.com",
            "password": "newpassword123",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["email"] == "newuser@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_login_returns_204_and_sets_shortist_cookie(async_client):
    await async_client.post(
        "/auth/register",
        json={"id": 1, "email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )
    response = await async_client.post(
        "/auth/jwt/login",
        data={"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )
    assert response.status_code == 204
    cookie_value = response.cookies.get("shortist")
    assert cookie_value
    assert len(cookie_value) > 20


async def test_logout_returns_204_and_clears_cookie(async_client, auth_token):
    async_client.cookies.set("shortist", auth_token)
    response = await async_client.post("/auth/jwt/logout")
    assert response.status_code == 204
    set_cookie_header = response.headers.get("set-cookie", "").lower()
    assert "shortist=" in set_cookie_header
    assert "max-age=0" in set_cookie_header or 'shortist=""' in set_cookie_header
