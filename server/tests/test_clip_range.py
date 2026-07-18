from clipper import is_whole_video


def test_full_selection_is_whole():
    assert is_whole_video(0, 19, 19) is True
    assert is_whole_video(1, 600, 600) is True


def test_partial_selection_is_not_whole():
    assert is_whole_video(0, 10, 19) is False
    assert is_whole_video(2, 19, 19) is False
    assert is_whole_video(0, 598, 600) is False


def test_unknown_duration_is_not_whole():
    assert is_whole_video(0, 19, None) is False
