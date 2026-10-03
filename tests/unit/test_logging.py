import io
import json
import logging

import pytest
import structlog

from ksef2._logging import configure_logging, get_logger


@pytest.fixture(autouse=True)
def reset_logging_state():
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level

    try:
        yield
    finally:
        structlog.reset_defaults()
        root_logger.handlers[:] = original_handlers
        root_logger.setLevel(original_level)


class TestPackageLogging:
    def test_configure_logging_emits_json_events(self) -> None:
        stream = io.StringIO()

        configure_logging(
            level="INFO",
            renderer="json",
            stream=stream,
            force=True,
        )

        get_logger().info("SDK logger configured", component="tests")

        payload = json.loads(stream.getvalue())
        assert payload["event"] == "SDK logger configured"
        assert payload["component"] == "tests"
        assert payload["level"] == "info"
        assert payload["logger"] == "ksef2"
        assert "timestamp" in payload

    def test_get_logger_uses_explicit_logger_name(self) -> None:
        stream = io.StringIO()

        configure_logging(
            level="INFO",
            renderer="json",
            stream=stream,
            force=True,
        )

        get_logger("ksef2.tests").warning("Named logger works")

        payload = json.loads(stream.getvalue())
        assert payload["event"] == "Named logger works"
        assert payload["logger"] == "ksef2.tests"
        assert payload["level"] == "warning"
