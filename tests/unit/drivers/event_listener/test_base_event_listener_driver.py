from tests.mocks.mock_event import MockEvent
from tests.mocks.mock_event_listener_driver import MockEventListenerDriver


class TestBaseEventListenerDriver:
    def test__safe_try_publish_event(self):
        driver = MockEventListenerDriver(batched=False)

        for _ in range(4):
            driver._safe_try_publish_event(MockEvent().to_dict(), flush=False)
        assert len(driver.batch) == 0

    def test__safe_try_publish_event_batch(self):
        driver = MockEventListenerDriver(batched=True)

        for _ in range(0, 3):
            driver._safe_try_publish_event(MockEvent().to_dict(), flush=False)
        assert len(driver.batch) == 3

    def test__safe_try_publish_event_batch_flush(self):
        driver = MockEventListenerDriver(batched=True)

        for _ in range(0, 3):
            driver._safe_try_publish_event(MockEvent().to_dict(), flush=True)
        assert len(driver.batch) == 0
