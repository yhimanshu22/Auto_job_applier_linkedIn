from routes.config_parse import (
    format_config_content,
    normalize_stored_value,
    parse_config_content,
    parse_config_value,
)


def test_parse_list_search_terms():
    assert parse_config_value("['Software Engineer','Python']", "search_terms") == [
        "Software Engineer",
        "Python",
    ]


def test_parse_corrupted_bracket_string():
    assert parse_config_value('"["', "search_terms") == []
    assert normalize_stored_value("search_terms", "[") == []
    assert normalize_stored_value("bad_words", "[") == []


def test_format_list_uses_json_style():
    text = format_config_content(
        "search",
        {
            "search_terms": ["Software Engineer"],
            "easy_apply_only": True,
            "search_location": "India",
        },
    )
    assert "search_terms = ['Software Engineer']" in text
    assert "easy_apply_only = True" in text
    assert 'search_location = "India"' in text


def test_roundtrip_search_config():
    original = """################ SEARCH CONFIGURATION ################

search_terms = ['Software Engineer','Backend Developer']
bad_words = ['Senior Director','10+ years']
job_type = ['Full-time']
search_location = "India"
easy_apply_only = True
switch_number = 30
"""
    parsed = parse_config_content(original)
    assert parsed["search_terms"] == ["Software Engineer", "Backend Developer"]
    assert parsed["bad_words"] == ["Senior Director", "10+ years"]
    assert parsed["job_type"] == ["Full-time"]

    exported = format_config_content("search", parsed)
    again = parse_config_content(exported)
    assert again["search_terms"] == parsed["search_terms"]
    assert again["bad_words"] == parsed["bad_words"]
