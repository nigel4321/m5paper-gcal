from src import device


def test_minutes_to_seconds():
    assert device.minutes_to_seconds(30) == 1_800
    assert device.minutes_to_seconds(1) == 60
    assert device.minutes_to_seconds(0) == 0
