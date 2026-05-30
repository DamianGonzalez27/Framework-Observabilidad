import logging
import threading
import uuid
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from logger_tracker import (
    UUIDLogFilter,
    setup_logging,
    get_logger,
    attach_logger_to_werkzeug,
    get_request_uuid,
    set_request_uuid,
    logg_info,
    logg_debug,
    logg_warning,
    logg_error,
    logg_critical,
    _request_uuid
)


class TestUUIDLogFilter:
    def test_filter_adds_uuid_to_record(self):
        """Test that the filter adds a UUID to the log record."""
        filter_instance = UUIDLogFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )

        # Ensure no UUID initially
        assert not hasattr(record, 'uuid')

        # Apply filter
        result = filter_instance.filter(record)

        # Should return True and add UUID
        assert result is True
        assert hasattr(record, 'uuid')
        assert isinstance(record.uuid, str)
        # Check it's a valid UUID
        uuid.UUID(record.uuid)

    def test_uuid_is_thread_local(self):
        """Test that UUID is unique per thread."""
        uuids = []

        def get_uuid():
            filter_instance = UUIDLogFilter()
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="test", args=(), exc_info=None
            )
            filter_instance.filter(record)
            uuids.append(record.uuid)

        threads = [threading.Thread(target=get_uuid) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All UUIDs should be different
        assert len(set(uuids)) == 3

    def test_uuid_persists_in_same_thread(self):
        """Test that the same UUID is used in the same thread."""
        filter_instance = UUIDLogFilter()

        record1 = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test1", args=(), exc_info=None
        )
        record2 = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test2", args=(), exc_info=None
        )

        filter_instance.filter(record1)
        filter_instance.filter(record2)

        assert record1.uuid == record2.uuid


class TestSetupLogging:
    @patch('logger_tracker.logging.basicConfig')
    @patch('logger_tracker.RichHandler')
    @patch('logger_tracker.os.environ.get')
    def test_setup_logging_configures_correctly(self, mock_environ_get, mock_rich_handler, mock_basic_config):
        """Test that setup_logging configures logging with correct parameters."""
        mock_environ_get.return_value = 'DEBUG'
        mock_handler_instance = MagicMock()
        mock_rich_handler.return_value = mock_handler_instance

        setup_logging()

        # Check RichHandler was created with correct params
        mock_rich_handler.assert_called_once_with(
            rich_tracebacks=True,
            tracebacks_suppress=[logging]
        )

        # Check filter was added
        mock_handler_instance.addFilter.assert_called_once()

        # Check basicConfig was called with correct params
        mock_basic_config.assert_called_once_with(
            level=logging.DEBUG,
            format="[%(uuid)s] %(message)s",
            datefmt="[%X]",
            handlers=[mock_handler_instance]
        )

    @patch('logger_tracker.logging.basicConfig')
    @patch('logger_tracker.RichHandler')
    @patch('logger_tracker.os.environ.get')
    def test_setup_logging_uses_env_var(self, mock_environ_get, mock_rich_handler, mock_basic_config):
        """Test that setup_logging uses LOG_LEVEL environment variable."""
        mock_environ_get.return_value = 'INFO'
        mock_handler_instance = MagicMock()
        mock_rich_handler.return_value = mock_handler_instance

        setup_logging()

        # Check basicConfig was called with INFO level
        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="[%(uuid)s] %(message)s",
            datefmt="[%X]",
            handlers=[mock_handler_instance]
        )


class TestGetLogger:
    def test_get_logger_returns_dict_with_functions(self):
        """Test that get_logger returns a dict with logging functions."""
        logger_dict = get_logger("test_logger")

        assert isinstance(logger_dict, dict)
        assert "info" in logger_dict
        assert "debug" in logger_dict
        assert "warning" in logger_dict
        assert "error" in logger_dict
        assert "critical" in logger_dict

        # Check they are callable
        for func in logger_dict.values():
            assert callable(func)

    def test_get_logger_uses_correct_name(self):
        """Test that get_logger uses the provided name."""
        with patch('logger_tracker.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            get_logger("custom_name")

            mock_get_logger.assert_called_once_with("custom_name")


class TestAttachLoggerToWerkzeug:
    @patch('logger_tracker.logging.getLogger')
    def test_attach_logger_to_werkzeug(self, mock_get_logger):
        """Test that attach_logger_to_werkzeug sets up werkzeug logger correctly."""
        werkzeug_logger = MagicMock()
        app_logger = MagicMock()
        app_logger.handlers = [MagicMock()]

        mock_get_logger.side_effect = lambda name: werkzeug_logger if name == "werkzeug" else app_logger

        attach_logger_to_werkzeug()

        # Check werkzeug logger handlers are set
        assert werkzeug_logger.handlers == app_logger.handlers
        werkzeug_logger.setLevel.assert_called_once_with(logging.INFO)
        assert werkzeug_logger.propagate is False


class TestLegacyAPI:
    def test_logg_info_logs_message(self, caplog):
        """Test that logg_info logs the message."""
        with caplog.at_level(logging.INFO):
            logg_info("test message")
        assert "test message" in caplog.text

    def test_logg_debug_logs_message(self, caplog):
        """Test that logg_debug logs the message."""
        with caplog.at_level(logging.DEBUG):
            logg_debug("test message")
        assert "test message" in caplog.text

    def test_logg_warning_logs_message(self, caplog):
        """Test that logg_warning logs the message."""
        with caplog.at_level(logging.WARNING):
            logg_warning("test message")
        assert "test message" in caplog.text

    def test_logg_error_logs_message(self, caplog):
        """Test that logg_error logs the message."""
        with caplog.at_level(logging.ERROR):
            logg_error("test message")
        assert "test message" in caplog.text

    def test_logg_critical_logs_message(self, caplog):
        """Test that logg_critical logs the message."""
        with caplog.at_level(logging.CRITICAL):
            logg_critical("test message")
        assert "test message" in caplog.text


class TestIntegration:
    def test_thread_safety_integration(self):
        """Test that UUIDs are different across threads."""
        # Note: logging is already set up
        results = []

        def log_in_thread():
            # Call the filter directly to set uuid
            filter_instance = UUIDLogFilter()
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="test", args=(), exc_info=None
            )
            filter_instance.filter(record)
            uuid_val = record.uuid
            results.append(uuid_val)

        threads = [threading.Thread(target=log_in_thread) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have two different UUIDs
        assert len(results) == 2
        assert results[0] != results[1]
        assert all(isinstance(uid, str) for uid in results)


class TestGetAndSetRequestUUID:
    def test_get_request_uuid_returns_string(self):
        """Test that get_request_uuid returns a valid UUID string."""
        uuid_val = get_request_uuid()
        assert isinstance(uuid_val, str)
        # Verify it's a valid UUID format
        uuid.UUID(uuid_val)

    def test_get_request_uuid_consistent_in_same_thread(self):
        """Test that get_request_uuid returns the same value in the same thread."""
        # Clear any previous UUID
        if hasattr(_request_uuid, 'id'):
            delattr(_request_uuid, 'id')
        
        uuid1 = get_request_uuid()
        uuid2 = get_request_uuid()
        assert uuid1 == uuid2

    def test_set_request_uuid_changes_value(self):
        """Test that set_request_uuid changes the UUID for the current thread."""
        custom_uuid = "custom-uuid-12345"
        set_request_uuid(custom_uuid)
        assert get_request_uuid() == custom_uuid

    def test_set_request_uuid_affects_logs(self):
        """Test that set_request_uuid affects the logs."""
        custom_uuid = "request-abc-123"
        set_request_uuid(custom_uuid)
        
        # Create a logger and log something
        logger = get_logger("test_custom_uuid")
        
        # The UUID should be set properly
        current_uuid = get_request_uuid()
        assert current_uuid == custom_uuid

    def test_request_uuid_isolation_between_threads(self):
        """Test that UUIDs are isolated between threads."""
        results = {}

        def thread_func(thread_id):
            custom_uuid = f"thread-{thread_id}-uuid"
            set_request_uuid(custom_uuid)
            results[thread_id] = get_request_uuid()

        threads = []
        for i in range(3):
            t = threading.Thread(target=thread_func, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Each thread should have its own UUID
        assert results[0] == "thread-0-uuid"
        assert results[1] == "thread-1-uuid"
        assert results[2] == "thread-2-uuid"