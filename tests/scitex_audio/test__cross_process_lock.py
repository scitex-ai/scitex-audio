#!/usr/bin/env python3
"""Tests for the cross-process audio playback lock.

No mocks: every test uses a real fcntl lock file under ``tmp_path``. The
``acquire_audio_lock`` context manager takes an explicit ``lock_file=``
seam so tests need not patch the module-level ``LOCK_FILE`` constant.
"""

import inspect
import os
import threading
import time

import pytest

from scitex_audio._cross_process_lock import AudioPlaybackLock, acquire_audio_lock


@pytest.fixture
def lock_path(tmp_path):
    return tmp_path / "test.lock"


class TestAudioPlaybackLockInit:
    def test_init_creates_instance(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock is not None

    def test_default_lock_file_is_set(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock.lock_file is not None

    def test_default_lock_file_is_under_audio_dir(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert "audio" in str(lock.lock_file)

    def test_custom_lock_file_is_used(self, lock_path):
        # Arrange
        # Act
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Assert
        assert lock.lock_file == lock_path

    def test_fd_starts_none(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock._fd is None

    def test_acquired_starts_false(self):
        # Arrange
        # Act
        lock = AudioPlaybackLock()
        # Assert
        assert lock._acquired is False


class TestEnsureLockDir:
    def test_creates_missing_parent_directory(self, tmp_path):
        # Arrange
        lock_path = tmp_path / "subdir" / "test.lock"
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        lock._ensure_lock_dir()
        # Assert
        assert lock_path.parent.exists()

    def test_existing_directory_is_idempotent(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock._ensure_lock_dir()
        # Act
        lock._ensure_lock_dir()
        # Assert
        assert lock_path.parent.exists()


class TestAcquire:
    def test_acquire_returns_true(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        result = lock.acquire()
        # Assert
        assert result is True
        lock.release()

    def test_acquire_sets_acquired_flag(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        lock.acquire()
        # Assert
        assert lock._acquired is True
        lock.release()

    def test_acquire_creates_lock_file(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        lock.acquire()
        # Assert
        assert lock_path.exists()
        lock.release()

    def test_acquire_writes_pid_to_file(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        lock.acquire()
        # Assert
        assert str(os.getpid()) in lock_path.read_text()
        lock.release()

    def test_second_acquirer_times_out_while_held(self, lock_path):
        # Arrange
        holder = AudioPlaybackLock(lock_file=lock_path)
        holder.acquire()
        contender = AudioPlaybackLock(lock_file=lock_path)
        # Act
        result = contender.acquire(timeout=0.2)
        # Assert
        assert result is False
        holder.release()

    def test_acquire_sets_integer_fd(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        lock.acquire()
        # Assert
        assert isinstance(lock._fd, int)
        lock.release()


class TestRelease:
    def test_release_clears_acquired_flag(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        # Act
        lock.release()
        # Assert
        assert lock._acquired is False

    def test_release_clears_fd(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        # Act
        lock.release()
        # Assert
        assert lock._fd is None

    def test_release_lets_next_acquirer_in(self, lock_path):
        # Arrange
        first = AudioPlaybackLock(lock_file=lock_path)
        first.acquire()
        first.release()
        second = AudioPlaybackLock(lock_file=lock_path)
        # Act
        result = second.acquire(timeout=0.5)
        # Assert
        assert result is True
        second.release()

    def test_release_without_acquire_is_safe(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        lock.release()
        # Assert
        assert lock._fd is None


class TestCleanup:
    def test_cleanup_closes_the_fd(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        fd = lock._fd
        # Act
        lock._cleanup()
        # Assert
        ctx = pytest.raises(OSError)
        with ctx:
            os.read(fd, 1)

    def test_cleanup_clears_fd_reference(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        # Act
        lock._cleanup()
        # Assert
        assert lock._fd is None

    def test_cleanup_handles_none_fd(self):
        # Arrange
        lock = AudioPlaybackLock()
        # Act
        lock._cleanup()
        # Assert
        assert lock._fd is None


class TestContextManager:
    def test_enter_acquires_lock(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        with lock:
            acquired = lock._acquired
        # Assert
        assert acquired is True

    def test_exit_clears_acquired_flag(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        with lock:
            pass
        # Assert
        assert lock._acquired is False

    def test_exit_clears_fd(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        with lock:
            pass
        # Assert
        assert lock._fd is None

    def test_exit_releases_even_on_exception(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        try:
            with lock:
                raise ValueError("boom")
        except ValueError:
            pass
        # Assert
        assert lock._acquired is False

    def test_exit_does_not_suppress_exceptions(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        result = lock.__exit__(None, None, None)
        # Assert
        assert result is False


class TestAcquireAudioLock:
    def test_yields_true_when_acquired(self, lock_path):
        # Arrange
        # Act
        with acquire_audio_lock(lock_file=lock_path) as result:
            acquired = result
        # Assert
        assert acquired is True

    def test_raises_timeout_error_when_held(self, lock_path):
        # Arrange
        holder = AudioPlaybackLock(lock_file=lock_path)
        holder.acquire()
        # Act
        ctx = pytest.raises(TimeoutError)
        # Assert
        try:
            with ctx:
                with acquire_audio_lock(timeout=0.2, lock_file=lock_path):
                    pass
        finally:
            holder.release()

    def test_releases_lock_after_context(self, lock_path):
        # Arrange
        with acquire_audio_lock(lock_file=lock_path):
            pass
        follow_up = AudioPlaybackLock(lock_file=lock_path)
        # Act
        result = follow_up.acquire(timeout=0.5)
        # Assert
        assert result is True
        follow_up.release()

    def test_default_timeout_is_sixty_seconds(self):
        # Arrange
        sig = inspect.signature(acquire_audio_lock)
        # Act
        timeout_default = sig.parameters["timeout"].default
        # Assert
        assert timeout_default == 60.0


class TestConcurrency:
    def test_two_threads_acquire_sequentially(self, lock_path):
        # Arrange
        results = []

        def acquire_and_record(name):
            lock = AudioPlaybackLock(lock_file=lock_path)
            if lock.acquire(timeout=2.0):
                results.append(f"{name}_acquired")
                time.sleep(0.1)
                results.append(f"{name}_released")
                lock.release()

        t1 = threading.Thread(target=acquire_and_record, args=("t1",))
        t2 = threading.Thread(target=acquire_and_record, args=("t2",))
        # Act
        t1.start()
        time.sleep(0.05)  # ensure t1 wins the race
        t2.start()
        t1.join()
        t2.join()
        # Assert
        assert results == [
            "t1_acquired",
            "t1_released",
            "t2_acquired",
            "t2_released",
        ]


class TestIntegration:
    def test_acquire_creates_and_marks_lock(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        # Act
        acquired = lock.acquire()
        # Assert
        assert (acquired, lock._acquired, lock_path.exists()) == (True, True, True)
        lock.release()

    def test_release_resets_state(self, lock_path):
        # Arrange
        lock = AudioPlaybackLock(lock_file=lock_path)
        lock.acquire()
        # Act
        lock.release()
        # Assert
        assert (lock._acquired, lock._fd) == (False, None)

    def test_context_manager_creates_lock_file(self, lock_path):
        # Arrange
        # Act
        with acquire_audio_lock(timeout=5.0, lock_file=lock_path):
            exists_during = lock_path.exists()
        # Assert
        assert exists_during is True


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])

# EOF
