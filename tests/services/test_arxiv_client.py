from datetime import datetime, timezone

import pytest

from backend.services.arxiv_client import build_search_query, parse_atom, validate_categories


def test_category_query_and_date_range():
    query = build_search_query(
        ["cs.AI", "cs.LG"],
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    assert query == "(cat:cs.AI OR cat:cs.LG) AND submittedDate:[202601010000 TO 202601020000]"


def test_category_validation_deduplicates_and_rejects_bad_values():
    assert validate_categories(["cs.AI", "cs.AI"]) == ["cs.AI"]
    with pytest.raises(ValueError):
        validate_categories(["not a category"])


def test_atom_parser_normalizes_metadata_and_versions():
    xml = b'''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>1</opensearch:totalResults><entry><id>http://arxiv.org/abs/2601.12345v2</id><title> A title\n here </title><summary> An abstract\n here </summary><author><name>A. Author</name></author><author><name>B. Author</name></author><published>2026-01-01T10:00:00Z</published><updated>2026-01-02T10:00:00Z</updated><category term="cs.AI"/><link rel="alternate" href="http://arxiv.org/abs/2601.12345v2"/></entry></feed>'''
    papers, total = parse_atom(xml)
    assert total == 1
    assert papers[0].arxiv_id == "2601.12345"
    assert papers[0].title == "A title here"
    assert papers[0].authors == "A. Author, B. Author"
    assert papers[0].url.startswith("https://")
