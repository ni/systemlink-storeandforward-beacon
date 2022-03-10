from datetime import datetime, timedelta
import json
import os
import tempfile
from typing import List
import uuid

from systemlink_storeandforward_beacon import _systemlink_storeandforward_inspector


def test_emptyDirectory_calculatePendingRequests_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        result = _systemlink_storeandforward_inspector.calculate_pending_requests(tempDir)

        assert result == 0


def test_noCacheFile_calculatePendingRequests_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        _write_sample_transaction_buffer(tempDir, [datetime.today()])

        result = _systemlink_storeandforward_inspector.calculate_pending_requests(tempDir)

        assert result == 0


def test_onlyAlreadyProcessedRequests_calculatePendingRequests_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        now = datetime.now()
        requestTimestamps = [
            now - timedelta(minutes=3),
            now - timedelta(minutes=2),
            now - timedelta(minutes=1),
        ]
        _write_sample_transaction_buffer(tempDir, requestTimestamps)
        _write_cache_file(tempDir, now)

        result = _systemlink_storeandforward_inspector.calculate_pending_requests(tempDir)

        assert result == 0


def test_mixOfProcessedAndPendingRequests_calculatePendingRequests_returnsPending():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        now = datetime.now()
        requestTimestamps1 = [
            now - timedelta(minutes=1),
            now + timedelta(minutes=1),
            now + timedelta(minutes=2),
        ]
        requestTimestamps2 = [
            now - timedelta(minutes=6),
            now - timedelta(minutes=5),
            now - timedelta(minutes=4),
        ]
        requestTimestamps3 = [
            now + timedelta(minutes=4),
            now + timedelta(minutes=5),
            now + timedelta(minutes=6),
        ]
        _write_sample_transaction_buffer(tempDir, requestTimestamps1)
        _write_sample_transaction_buffer(tempDir, requestTimestamps2)
        _write_sample_transaction_buffer(tempDir, requestTimestamps3)
        _write_cache_file(tempDir, now)

        result = _systemlink_storeandforward_inspector.calculate_pending_requests(tempDir)

        assert result == 5


def test_realRequestTransactionsBuffer_calculatePendingRequests_returnsPending():
    storeDirectory = os.path.join(os.path.dirname(__file__), "testmon")
    result = _systemlink_storeandforward_inspector.calculate_pending_requests(storeDirectory)

    assert result == 0


def test_missingQuarantineDirectory_calculateQuaratineRequests_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        result = _systemlink_storeandforward_inspector.calculate_quaratine_requests(tempDir)

        assert result == 0


def test_emptyQuarantineDirectory_calculateQuaratineRequests_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        os.mkdir(os.path.join(tempDir, "quarantine"))
        result = _systemlink_storeandforward_inspector.calculate_quaratine_requests(tempDir)

        assert result == 0


def test_requestsQuarantined_calculateQuaratineRequests_returnsQuarantined():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        quarantineDirectory = os.path.join(tempDir, "quarantine")
        os.mkdir(quarantineDirectory)
        now = datetime.now()
        requestTimestamps1 = [
            now - timedelta(minutes=1),
            now + timedelta(minutes=1),
            now + timedelta(minutes=2),
        ]
        requestTimestamps2 = [
            now - timedelta(minutes=6),
            now - timedelta(minutes=5),
            now - timedelta(minutes=4),
        ]
        requestTimestamps3 = [
            now + timedelta(minutes=4),
            now + timedelta(minutes=5),
            now + timedelta(minutes=6),
        ]
        _write_sample_transaction_buffer(quarantineDirectory, requestTimestamps1)
        _write_sample_transaction_buffer(quarantineDirectory, requestTimestamps2)
        _write_sample_transaction_buffer(quarantineDirectory, requestTimestamps3)

        result = _systemlink_storeandforward_inspector.calculate_quaratine_requests(tempDir)

        assert result == 9


def test_realRequestTransactionsBuffer_calculateQuaratineRequests_returnsQuarantined():
    storeDirectory = os.path.join(os.path.dirname(__file__), "testmon")
    result = _systemlink_storeandforward_inspector.calculate_quaratine_requests(storeDirectory)

    assert result == 62


def _write_sample_transaction_buffer(directory: str, requestTimestamps: List[datetime]):
    lines = map(
        lambda t: json.dumps({"timestamp": datetime.isoformat(t)}, indent=None) + "\n",
        requestTimestamps,
    )
    filename = str(uuid.uuid1()) + ".jsonl"
    with open(os.path.join(directory, filename), "x") as fp:
        fp.writelines(lines)


def _write_cache_file(directory: str, timestamp: datetime):
    contents = json.dumps({"timestamp": datetime.isoformat(timestamp)}, indent=None)
    with open(os.path.join(directory, "__CACHE__"), "x") as fp:
        fp.write(contents)
