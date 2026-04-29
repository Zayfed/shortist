from sqlalchemy import select

from src.links.crud import (
    create_link,
    get_link_by_short_id,
    increment_click_count,
    search_links,
)
from src.links.models import Link


async def test_create_link_anonymous_returns_link_with_generated_short_id(db_session):
    link = await create_link(db_session, original_url="https://example.com")
    assert link.id is not None
    assert link.short_id is not None
    assert len(link.short_id) == 6
    assert link.original_url == "https://example.com"
    assert link.user_id is None
    assert link.click_count == 0


async def test_get_link_by_short_id_returns_existing(db_session):
    created = await create_link(db_session, original_url="https://example.com")
    found = await get_link_by_short_id(db_session, created.short_id)
    assert found is not None
    assert found.id == created.id


async def test_get_link_by_short_id_returns_none_for_missing(db_session):
    found = await get_link_by_short_id(db_session, "nonexistent")
    assert found is None


async def test_increment_click_count_persists_change(db_session):
    link = await create_link(db_session, original_url="https://example.com")
    await increment_click_count(db_session, link)
    await increment_click_count(db_session, link)

    result = await db_session.execute(
        select(Link).where(Link.short_id == link.short_id)
    )
    assert result.scalar_one().click_count == 2


async def test_search_links_filters_by_user_id(db_session):
    await create_link(db_session, original_url="https://example.com/foo", user_id=1)
    await create_link(db_session, original_url="https://example.com/bar", user_id=2)

    results = await search_links(db_session, original_url="example.com", user_id=1)
    assert len(results) == 1
    assert results[0].user_id == 1
