from datetime import datetime, timedelta, timezone

from src.links.schemas import LinkUpdate


def test_link_update_round_expire_at_drops_seconds_and_microseconds():
    raw = (datetime.now(timezone.utc) + timedelta(days=10)).replace(second=42, microsecond=987654)
    update = LinkUpdate(expire_at=raw)
    assert update.expire_at.second == 0
    assert update.expire_at.microsecond == 0
