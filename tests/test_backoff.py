"""Tests for voltricx.backoff — targeting 100% branch coverage."""

from voltricx.backoff import Backoff


def test_backoff_initial_state():
    b = Backoff()
    assert b.base == 1
    assert b.maximum == 30.0
    assert b.max_tries == 5
    assert b.retries == 1
    assert b._last_wait == 0


def test_backoff_custom_params():
    b = Backoff(base=2, maximum=60.0, max_tries=10)
    assert b.base == 2
    assert b.maximum == 60.0
    assert b.max_tries == 10


def test_backoff_calculate_returns_float():
    b = Backoff()
    wait = b.calculate()
    assert isinstance(wait, float)
    assert wait >= 0


def test_backoff_calculate_does_not_exceed_maximum():
    b = Backoff(base=1, maximum=5.0, max_tries=None)
    for _ in range(20):
        wait = b.calculate()
        assert wait <= 5.0


def test_backoff_reset():
    b = Backoff()
    b.calculate()
    b.calculate()
    b.reset()
    assert b.retries == 1
    assert b._last_wait == 0


def test_backoff_resets_after_max_tries():
    b = Backoff(base=1, maximum=100.0, max_tries=3)
    for _ in range(3):
        b.calculate()
    # After max_tries exhausted, retries resets
    assert b.retries == 1


def test_backoff_indefinite_run():
    """max_tries=None should never reset due to retries."""
    b = Backoff(base=1, maximum=30.0, max_tries=None)
    # Run many times — should not crash or exceed maximum
    for _ in range(50):
        wait = b.calculate()
        assert wait <= 30.0


def test_backoff_wait_doubles_when_below_last():
    """Forces the wait < _last_wait branch."""
    b = Backoff(base=1, maximum=1000.0, max_tries=None)
    # Manually set a very high last_wait so random wait will be < last_wait
    b._last_wait = 999.0
    b.retries = 1
    wait = b.calculate()
    # Should double the last_wait (999.0 * 2 = 1998.0) but capped at maximum
    assert wait <= 1000.0


def test_backoff_resets_on_exceeding_maximum():
    """When wait > maximum, retries and _last_wait reset."""
    b = Backoff(base=1, maximum=0.001, max_tries=None)
    b._last_wait = 999.0  # force doubling path
    b.retries = 1
    b.calculate()
    # After exceeding maximum, state should reset
    assert b._last_wait == 0
    assert b.retries == 1
