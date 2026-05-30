from src import device


def test_minutes_to_ms():
    assert device.minutes_to_ms(30) == 1_800_000
    assert device.minutes_to_ms(1) == 60_000
    assert device.minutes_to_ms(0) == 0
