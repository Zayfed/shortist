import string

from src.links.crud import generate_short_id


def test_short_id_default_length_and_alphabet():
    allowed = set(string.ascii_letters + string.digits)
    for _ in range(50):
        sid = generate_short_id()
        assert len(sid) == 6
        assert set(sid) <= allowed
