#!/usr/bin/env python3
"""Tests for CrossProcessLock module."""

import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scitex_audio._cross_process_lock import AudioPlaybackLock, acquire_audio_lock


class TestAudioPlaybackLockInit:
    """Tests for AudioPlaybackLock initialization."""

    def test_init_creates_instance(self):
        """AudioPlaybackLock should initialize without errors."""
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock is not None

    def test_init_uses_default_lock_file_lock_lock_file_is_not_none(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Act
        # Assert
        assert lock.lock_file is not None

    def test_init_uses_default_lock_file_audio_in_str_lock_lock_file(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Act
        # Assert
        assert "audio" in str(lock.lock_file)

    def test_init_uses_custom_lock_file(self):
        """Should use custom lock file when provided."""
        # Arrange
        custom_path = Path("/tmp/custom.lock")
        # Act
        lock = AudioPlaybackLock(lock_file=custom_path)
        # Assert
        assert lock.lock_file == custom_path

    def test_init_sets_fd_to_none(self):
        """Should initialize _fd to None."""
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock._fd is None

    def test_init_sets_acquired_to_false(self):
        """Should initialize _acquired to False."""
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock._acquired is False


class TestEnsureLockDir:
    """Tests for _ensure_lock_dir method."""

    def test_creates_parent_directory(self):
        """Should create parent directory if it doesn't exist."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "subdir" / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            lock._ensure_lock_dir()
            assert lock_path.parent.exists()

    def test_handles_existing_directory(self):
        """Should not raise if directory already exists."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            # Should not raise
            lock._ensure_lock_dir()
            lock._ensure_lock_dir()  # Call again
            assert lock_path.parent.exists()


class TestAcquire:
    """Tests for acquire method."""

    def test_acquire_returns_true(self):
        """Should return True when lock acquired."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            result = lock.acquire()
            assert result is True
            lock.release()

    def test_acquire_sets_acquired_flag(self):
        """Should set _acquired to True after acquiring."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            lock.acquire()
            assert lock._acquired is True
            lock.release()

    def test_acquire_creates_lock_file(self):
        """Should create lock file."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            lock.acquire()
            assert lock_path.exists()
            lock.release()

    def test_acquire_writes_pid_to_file(self):
        """Should write PID to lock file."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            lock.acquire()
            content = lock_path.read_text()
            assert str(os.getpid()) in content
            lock.release()

    def test_acquire_with_timeout_returns_false_on_timeout(self):
        """Should return False when timeout expires."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"

            # First lock holds it
            lock1 = AudioPlaybackLock(lock_file=lock_path)
            lock1.acquire()

            # Second lock times out
            lock2 = AudioPlaybackLock(lock_file=lock_path)
            result = lock2.acquire(timeout=0.2)

            assert result is False
            lock1.release()

    def test_acquire_sets_fd(self):
        """Should set _fd to valid file descriptor."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            lock.acquire()
            assert (lock._fd is not None) and (isinstance(lock._fd, int))
            lock.release()


class TestRelease:
    """Tests for release method."""

    def test_release_clears_acquired_flag(self):
        """Should clear _acquired flag."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            lock.acquire()
            lock.release()
            assert lock._acquired is False

    def test_release_clears_fd(self):
        """Should clear _fd to None."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            lock.acquire()
            lock.release()
            assert lock._fd is None

    def test_release_allows_another_process_to_acquire(self):
        """Should allow another lock to acquire after release."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"

            lock1 = AudioPlaybackLock(lock_file=lock_path)
            lock1.acquire()
            lock1.release()

            lock2 = AudioPlaybackLock(lock_file=lock_path)
            result = lock2.acquire(timeout=0.5)
            assert result is True
            lock2.release()

    def test_release_without_acquire_is_safe(self):
        """Should not raise when releasing without acquiring."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            # Should not raise
            lock.release()
            assert lock._fd is None


class TestCleanup:
    """Tests for _cleanup method."""

    def test_cleanup_closes_fd(self):
        """Should close file descriptor."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            lock.acquire()
            fd = lock._fd
            lock._cleanup()
            # Verify fd cleared and underlying fd is closed
            fd_still_valid = True
            try:
                os.read(fd, 1)
            except OSError:
                fd_still_valid = False
            assert lock._fd is None and not fd_still_valid

    def test_cleanup_handles_none_fd(self):
        """Should handle None _fd gracefully."""
        # Arrange
        # Act
        # Assert
        lock = AudioPlaybackLock()
        # Should not raise
        lock._cleanup()
        assert lock._fd is None


class TestContextManager:
    """Tests for context manager support."""

    def test_enter_acquires_lock(self):
        """__enter__ should acquire the lock."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            with lock:
                assert lock._acquired is True

    def test_exit_releases_lock(self):
        """__exit__ should release the lock."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            with lock:
                pass
            assert (lock._acquired is False) and (lock._fd is None)

    def test_exit_releases_on_exception(self):
        """__exit__ should release lock even on exception."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            try:
                with lock:
                    raise ValueError("Test exception")
            except ValueError:
                pass
            assert lock._acquired is False

    def test_exit_returns_false(self):
        """__exit__ should return False (not suppress exceptions)."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock = AudioPlaybackLock(lock_file=lock_path)
            result = lock.__exit__(None, None, None)
            assert result is False


class TestAcquireAudioLock:
    """Tests for acquire_audio_lock context manager function."""

    def test_yields_true_when_acquired(self):
        """Should yield True when lock is acquired."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "scitex_audio._cross_process_lock.LOCK_FILE",
                Path(tmpdir) / "test.lock",
            ):
                with acquire_audio_lock() as result:
                    assert result is True

    def test_raises_timeout_error_on_timeout(self):
        """Should raise TimeoutError when timeout expires."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"

            # Hold the lock
            holding_lock = AudioPlaybackLock(lock_file=lock_path)
            holding_lock.acquire()

            try:
                with patch(
                    "scitex_audio._cross_process_lock.LOCK_FILE",
                    lock_path,
                ):
                    with pytest.raises(TimeoutError) as excinfo:
                        with acquire_audio_lock(timeout=0.2):
                            pass
                    assert "0.2s" in str(excinfo.value)
            finally:
                holding_lock.release()

    def test_releases_lock_after_context(self):
        """Should release lock after context exits."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"

            with patch(
                "scitex_audio._cross_process_lock.LOCK_FILE",
                lock_path,
            ):
                with acquire_audio_lock():
                    pass

            # Should be able to acquire again
            lock = AudioPlaybackLock(lock_file=lock_path)
            result = lock.acquire(timeout=0.5)
            assert result is True
            lock.release()

    def test_default_timeout_is_60_seconds(self):
        """Should use 60 second default timeout."""
        # This is a specification test - we verify the function signature
        # Arrange
        import inspect

        sig = inspect.signature(acquire_audio_lock)
        # Act
        timeout_param = sig.parameters["timeout"]
        # Assert
        assert timeout_param.default == 60.0


class TestConcurrency:
    """Tests for concurrent lock acquisition."""

    def test_sequential_acquisition_smoke_case(self):
        """Locks should be acquired sequentially."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            results = []

            def acquire_and_record(name):
                lock = AudioPlaybackLock(lock_file=lock_path)
                if lock.acquire(timeout=2.0):
                    results.append(f"{name}_acquired")
                    time.sleep(0.1)
                    results.append(f"{name}_released")
                    lock.release()

            # Start first thread
            t1 = threading.Thread(target=acquire_and_record, args=("t1",))
            t2 = threading.Thread(target=acquire_and_record, args=("t2",))

            t1.start()
            time.sleep(0.05)  # Ensure t1 starts first
            t2.start()

            t1.join()
            t2.join()

            # Both should complete
            assert (len(results) == 4) and (results[0] == "t1_acquired")


class TestIntegration:
    """Integration tests for AudioPlaybackLock."""

    def test_full_lifecycle_smoke_case(self):
        """Test complete lock lifecycle."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"

            # Create and acquire
            lock = AudioPlaybackLock(lock_file=lock_path)
            assert (
                (lock.acquire() is True)
                and (lock._acquired is True)
                and (lock_path.exists())
            )

            # Release
            lock.release()
            assert (lock._acquired is False) and (lock._fd is None)

    def test_context_manager_lifecycle(self):
        """Test complete context manager lifecycle."""
        # Arrange
        # Act
        # Assert
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"

            with patch(
                "scitex_audio._cross_process_lock.LOCK_FILE",
                lock_path,
            ):
                with acquire_audio_lock(timeout=5.0) as acquired:
                    assert (acquired is True) and (lock_path.exists())


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
