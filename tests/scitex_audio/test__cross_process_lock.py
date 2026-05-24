#!/usr/bin/env python3
"""Tests for CrossProcessLock module.

Rewritten to honour the no-mocks rule. The two `patch(...)` calls in
the prior file were used to redirect `acquire_audio_lock`'s default
lock-file path; we now pass the path explicitly via the new
`lock_file=` kwarg on `acquire_audio_lock`. All other test bodies
already used real filesystem state via `tempfile.TemporaryDirectory`
and just needed structural cleanup (AAA, one-assert, descriptive
names).
"""

import os
import tempfile
import threading
import time
from pathlib import Path

import pytest

from scitex_audio._cross_process_lock import AudioPlaybackLock, acquire_audio_lock


class TestAudioPlaybackLockInit:
    """Tests for AudioPlaybackLock initialization."""

    def test_default_init_returns_non_none_instance(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock is not None

    def test_default_init_uses_non_none_lock_file_path(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock.lock_file is not None

    def test_default_init_lock_file_path_mentions_audio(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert "audio" in str(lock.lock_file)

    def test_init_with_custom_lock_file_uses_supplied_path(self):
        # Arrange
        custom_path = Path("/tmp/custom.lock")
        # Act
        lock = AudioPlaybackLock(lock_file=custom_path)
        # Assert
        assert lock.lock_file == custom_path

    def test_init_sets_underlying_fd_to_none(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock._fd is None

    def test_init_marks_lock_as_not_yet_acquired(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock._acquired is False


class TestEnsureLockDir:
    """Tests for _ensure_lock_dir method."""

    def test_creates_missing_parent_directory(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "subdir" / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        lock._ensure_lock_dir()
        # Assert
        assert lock_path.parent.exists()

    def test_idempotent_on_existing_parent_directory(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock._ensure_lock_dir()
        # Act
        lock._ensure_lock_dir()
        # Assert
        assert lock_path.parent.exists()


class TestAcquire:
    """Tests for acquire method."""

    def test_acquire_returns_true_on_success(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            result = lock.acquire()
        finally:
            lock.release()
        # Assert
        assert result is True

    def test_acquire_sets_acquired_flag_to_true(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            lock.acquire()
            value = lock._acquired
        finally:
            lock.release()
        # Assert
        assert value is True

    def test_acquire_creates_lock_file_on_disk(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            lock.acquire()
            exists = lock_path.exists()
        finally:
            lock.release()
        # Assert
        assert exists is True

    def test_acquire_writes_current_pid_into_lock_file(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            lock.acquire()
            content = lock_path.read_text()
        finally:
            lock.release()
        # Assert
        assert str(os.getpid()) in content

    def test_acquire_with_short_timeout_returns_false_when_held(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock1 = AudioPlaybackLock(lock_file=lock_path)
        lock1.acquire()
        lock2 = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            result = lock2.acquire(timeout=0.2)
        finally:
            lock1.release()
        # Assert
        assert result is False

    def test_acquire_sets_integer_fd(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            lock.acquire()
            fd_value = lock._fd
        finally:
            lock.release()
        # Assert
        assert isinstance(fd_value, int)


class TestRelease:
    """Tests for release method."""

    def test_release_clears_acquired_flag(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        # Act
        lock.release()
        # Assert
        assert lock._acquired is False

    def test_release_clears_fd_to_none(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        # Act
        lock.release()
        # Assert
        assert lock._fd is None

    def test_release_allows_subsequent_acquire(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock1 = AudioPlaybackLock(lock_file=lock_path)
        lock1.acquire()
        lock1.release()
        lock2 = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            result = lock2.acquire(timeout=0.5)
        finally:
            lock2.release()
        # Assert
        assert result is True

    def test_release_without_prior_acquire_is_safe(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        lock.release()
        # Assert
        assert lock._fd is None


class TestCleanup:
    """Tests for _cleanup method."""

    def test_cleanup_clears_fd_attribute(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        # Act
        lock._cleanup()
        # Assert
        assert lock._fd is None

    def test_cleanup_closes_underlying_descriptor(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        fd = lock._fd
        lock._cleanup()
        # Act
        try:
            os.read(fd, 1)
            fd_still_valid = True
        except OSError:
            fd_still_valid = False
        # Assert
        assert fd_still_valid is False

    def test_cleanup_safe_when_no_fd_held(self):
        # Arrange
        lock = AudioPlaybackLock()
        # Act
        lock._cleanup()
        # Assert
        assert lock._fd is None


class TestContextManager:
    """Tests for context manager support."""

    def test_enter_acquires_lock_inside_with_block(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        with lock:
            inside = lock._acquired
        # Assert
        assert inside is True

    def test_exit_clears_acquired_flag(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        with lock:
            pass
        # Assert
        assert lock._acquired is False

    def test_exit_releases_lock_even_on_exception(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            with lock:
                raise ValueError("Test exception")
        except ValueError:
            pass
        # Assert
        assert lock._acquired is False

    def test_exit_returns_false_to_not_suppress(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        result = lock.__exit__(None, None, None)
        # Assert
        assert result is False


class TestAcquireAudioLock:
    """Tests for acquire_audio_lock context manager function."""

    def test_yields_true_when_lock_acquired(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        # Act
        with acquire_audio_lock(lock_file=lock_path) as result:
            value = result
        # Assert
        assert value is True

    def test_raises_timeout_error_when_held_elsewhere(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        holding_lock = AudioPlaybackLock(lock_file=lock_path)
        holding_lock.acquire()
        # Act
        ctx = pytest.raises(TimeoutError, match="0.2s")
        # Assert
        try:
            with ctx:
                with acquire_audio_lock(timeout=0.2, lock_file=lock_path):
                    pass
        finally:
            holding_lock.release()

    def test_releases_lock_after_context_block_exits(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        with acquire_audio_lock(lock_file=lock_path):
            pass
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            result = lock.acquire(timeout=0.5)
        finally:
            lock.release()
        # Assert
        assert result is True

    def test_default_timeout_signature_is_sixty_seconds(self):
        # Arrange
        import inspect

        sig = inspect.signature(acquire_audio_lock)
        # Act
        timeout_default = sig.parameters["timeout"].default
        # Assert
        assert timeout_default == 60.0


class TestConcurrency:
    """Tests for concurrent lock acquisition."""

    def test_sequential_acquisition_first_thread_acquires_first(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        results: list[str] = []

        def acquire_and_record(name):
            lock = AudioPlaybackLock(lock_file=lock_path)
            if lock.acquire(timeout=2.0):
                results.append(f"{name}_acquired")
                time.sleep(0.1)
                results.append(f"{name}_released")
                lock.release()

        t1 = threading.Thread(target=acquire_and_record, args=("t1",))
        t2 = threading.Thread(target=acquire_and_record, args=("t2",))
        t1.start()
        time.sleep(0.05)
        t2.start()
        # Act
        t1.join()
        t2.join()
        # Assert
        assert results[0] == "t1_acquired"


class TestIntegration:
    """Integration tests for AudioPlaybackLock."""

    def test_full_lifecycle_acquire_creates_lock_file_on_disk(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            lock.acquire()
            exists = lock_path.exists()
        finally:
            lock.release()
        # Assert
        assert exists is True

    def test_context_manager_lifecycle_creates_lock_file_on_disk(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "test.lock"
        # Act
        with acquire_audio_lock(timeout=5.0, lock_file=lock_path):
            exists_during = lock_path.exists()
        # Assert
        assert exists_during is True


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
