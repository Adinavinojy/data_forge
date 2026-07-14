from app.services.nlp_service import is_help_query


def test_is_help_query_matches_normal_phrase():
    assert is_help_query("what is this")
    assert is_help_query("what is this?")


def test_is_help_query_matches_common_typo():
    assert is_help_query("wht is this")


def test_is_help_query_rejects_real_command():
    assert not is_help_query("drop duplicates")
