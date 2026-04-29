from datetime import datetime, timedelta, timezone

import pytest

from src.links.models import Link


def _past_iso() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).replace(microsecond=0).isoformat()


async def _create_link_as(client, token: str, url: str) -> str:
    client.cookies.set("shortist", token)
    response = await client.post(
        "/links/shorten",
        json={"original_url": url, "expire_at": None},
    )
    assert response.status_code == 200
    return response.json()["short_id"]


async def test_shorten_duplicate_custom_alias_returns_400(async_client, db_session):
    seeded = Link(
        original_url="https://example.com/first",
        short_id="dupseed",
        custom_alias="dupalias",
    )
    db_session.add(seeded)
    await db_session.commit()

    response = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/second",
            "custom_alias": "dupalias",
            "expire_at": None,
        },
    )
    assert response.status_code == 400
    assert "dupalias" in response.text


@pytest.mark.parametrize("alias", ["abc", "a" * 17, "ab cd"])
async def test_shorten_invalid_alias_length_or_pattern_returns_422(async_client, alias):
    response = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "custom_alias": alias,
            "expire_at": None,
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "bad_url",
    ["", "http://", "not a url at all", "://broken", "javascript:alert(1)"],
)
async def test_shorten_invalid_url_returns_422(async_client, bad_url):
    response = await async_client.post(
        "/links/shorten",
        json={
            "original_url": bad_url,
            "expire_at": None,
        },
    )
    assert response.status_code == 422


async def test_shorten_with_past_expire_at_returns_422(async_client):
    response = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "expire_at": _past_iso(),
        },
    )
    assert response.status_code == 422


async def test_redirect_nonexistent_short_id_returns_404(async_client):
    response = await async_client.get("/links/doesnotexist123")
    assert response.status_code == 404


async def test_stats_without_auth_returns_401(async_client, auth_token):
    short_id = await _create_link_as(async_client, auth_token, "https://example.com/private")

    async_client.cookies.clear()
    response = await async_client.get(f"/links/{short_id}/stats")
    assert response.status_code == 401


async def test_stats_other_user_link_returns_404(async_client, auth_token, second_auth_token):
    short_id = await _create_link_as(async_client, auth_token, "https://example.com/owned-by-first")

    async_client.cookies.clear()
    async_client.cookies.set("shortist", second_auth_token)
    response = await async_client.get(f"/links/{short_id}/stats")
    assert response.status_code == 404


async def test_delete_without_auth_returns_401(async_client, auth_token):
    short_id = await _create_link_as(async_client, auth_token, "https://example.com/del-noauth")

    async_client.cookies.clear()
    response = await async_client.delete(f"/links/{short_id}")
    assert response.status_code == 401


async def test_delete_other_user_link_returns_404(async_client, auth_token, second_auth_token):
    short_id = await _create_link_as(async_client, auth_token, "https://example.com/del-other")

    async_client.cookies.clear()
    async_client.cookies.set("shortist", second_auth_token)
    response = await async_client.delete(f"/links/{short_id}")
    assert response.status_code == 404


async def test_put_without_auth_returns_401(async_client, auth_token):
    short_id = await _create_link_as(async_client, auth_token, "https://example.com/put-noauth")

    async_client.cookies.clear()
    response = await async_client.put(
        f"/links/{short_id}",
        json={"original_url": "https://newtarget.example.com"},
    )
    assert response.status_code == 401


async def test_put_other_user_link_returns_404(async_client, auth_token, second_auth_token):
    short_id = await _create_link_as(async_client, auth_token, "https://example.com/put-other")

    async_client.cookies.clear()
    async_client.cookies.set("shortist", second_auth_token)
    response = await async_client.put(
        f"/links/{short_id}",
        json={"original_url": "https://hijack.example.com"},
    )
    assert response.status_code == 404
