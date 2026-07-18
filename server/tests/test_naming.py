from main import safe_name


def test_keeps_plain_title():
    assert safe_name("Hello World", "mp4") == "Hello World.mp4"


def test_strips_illegal_characters():
    assert safe_name("a/b:c*d?", "mp3") == "abcd.mp3"


def test_falls_back_when_empty():
    assert safe_name("", "gif") == "clip.gif"
    assert safe_name(None, "mp4") == "clip.mp4"
    assert safe_name("   ", "mp4") == "clip.mp4"


def test_truncates_long_title():
    assert safe_name("x" * 200, "mp4") == "x" * 80 + ".mp4"


def test_keeps_unicode_word_characters():
    assert safe_name("café ☕", "mp4") == "café.mp4"
