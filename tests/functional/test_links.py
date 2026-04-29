from sqlalchemy import select

from src.links.models import Link
from tests.conftest import TEST_USER_ID


async def test_shorten_anonymous_returns_200_and_short_id(async_client):
    response = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "expire_at": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["short_id"]
    assert len(body["short_id"]) == 6
    assert str(body["original_url"]).startswith("https://example.com")


async def test_shorten_with_custom_alias_uses_alias_as_short_id(async_client):
    response = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com",
            "custom_alias": "myalias",
            "expire_at": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["short_id"] == "myalias"


async def test_redirect_returns_307_with_location_header(async_client):
    create = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/page",
            "expire_at": None,
        },
    )
    short_id = create.json()["short_id"]

    response = await async_client.get(f"/links/{short_id}")
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://example.com/page")


async def test_redirect_increments_click_count(async_client, db_session):
    create = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/click",
            "expire_at": None,
        },
    )
    short_id = create.json()["short_id"]

    for _ in range(3):
        await async_client.get(f"/links/{short_id}")

    result = await db_session.execute(
        select(Link).where(Link.short_id == short_id)
    )
    link = result.scalar_one()
    assert link.click_count == 3


async def test_shorten_authorized_sets_user_id_in_db(async_client, auth_token, db_session):
    async_client.cookies.set("shortist", auth_token)
    response = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/owned",
            "expire_at": None,
        },
    )
    assert response.status_code == 200
    short_id = response.json()["short_id"]

    result = await db_session.execute(
        select(Link).where(Link.short_id == short_id)
    )
    link = result.scalar_one()
    assert link.user_id == TEST_USER_ID


async def test_stats_owner_returns_correct_click_count(async_client, auth_token):
    async_client.cookies.set("shortist", auth_token)
    create = await async_client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/stats",
            "expire_at": None,
        },
    )
    short_id = create.json()["short_id"]

    await async_client.get(f"/links/{short_id}")
    await async_client.get(f"/links/{short_id}")

    response = await async_client.get(f"/links/{short_id}/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["short_id"] == short_id
    assert body["click_count"] == 2
    assert str(body["original_url"]).startswith("https://example.com/stats")
    assert "created_at" in body


async def test_search_returns_owner_links_matching_substring(async_client, auth_token):
    async_client.cookies.set("shortist", auth_token)
    await async_client.post(
        "/links/shorten",
        json={"original_url": "https://example.com/foo", "expire_at": None},
    )
    await async_client.post(
        "/links/shorten",
        json={"original_url": "https://example.com/bar", "expire_at": None},
    )
    await async_client.post(
        "/links/shorten",
        json={"original_url": "https://other.org/baz", "expire_at": None},
    )

    response = await async_client.get(
        "/links/search/",
        params={"original_url": "example.com"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert all("example.com" in str(item["original_url"]) for item in body)


async def test_put_update_link_owner_changes_original_url(async_client, auth_token):
    async_client.cookies.set("shortist", auth_token)
    create = await async_client.post(
        "/links/shorten",
        json={"original_url": "https://old.example.com", "expire_at": None},
    )
    short_id = create.json()["short_id"]

    response = await async_client.put(
        f"/links/{short_id}",
        json={"original_url": "https://new.example.com"},
    )
    assert response.status_code == 200
    body = response.json()
    assert str(body["original_url"]).startswith("https://new.example.com")


async def test_delete_link_owner_returns_success_and_removes_record(
    async_client, auth_token, db_session
):
    async_client.cookies.set("shortist", auth_token)
    create = await async_client.post(
        "/links/shorten",
        json={"original_url": "https://example.com/delete-me", "expire_at": None},
    )
    short_id = create.json()["short_id"]

    response = await async_client.delete(f"/links/{short_id}")
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    result = await db_session.execute(
        select(Link).where(Link.short_id == short_id)
    )
    assert result.scalar_one_or_none() is None
