from main import friendly_error


def test_bot_block_is_friendly():
    raw = "ERROR: [youtube] abc: Sign in to confirm you're not a bot. Use --cookies-from-browser"
    msg = friendly_error(Exception(raw))
    assert "blocking downloads" in msg
    assert "--cookies" not in msg  # raw yt-dlp noise stripped out


def test_unavailable_video():
    assert friendly_error(Exception("ERROR: Video unavailable")) == "That video is unavailable or private."


def test_unknown_error_is_trimmed():
    assert friendly_error(Exception("ERROR: something odd happened")).startswith("something odd")
