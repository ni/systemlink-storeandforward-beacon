from datetime import datetime, timedelta
import json
import os
import tempfile
from typing import List, Tuple
import uuid

from systemlink_storeandforward_beacon import _systemlink_storeandforward_inspector


def test_emptyDirectory_calculatePendingFiles_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        result = _systemlink_storeandforward_inspector.calculate_pending_files(tempDir)

        assert result == 0


def test_filesPending_calculatePendingFiles_returnsPartialCount():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        _write_sample_pending_file(tempDir)
        _write_sample_pending_file(tempDir)
        _write_sample_pending_file(tempDir)

        result = _systemlink_storeandforward_inspector.calculate_pending_files(tempDir)

        assert result == 3


def test_realRequestTransactionsBuffer_calculatePendingRequestSize_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        result = _systemlink_storeandforward_inspector.calculate_pending_request_size(tempDir)

    assert result == (0, 0)


def test_someRequestsPending_calculatePendingRequestSize_returnsCountAndSize():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        now = datetime.now()
        requests = [
            (now - timedelta(minutes=3), "ResultCreateRequest"),
            (now - timedelta(minutes=2), "ResultUpdateRequest"),
            (now - timedelta(minutes=1), "ResultUpdateRequest"),
        ]
        _write_sample_transaction_buffer(tempDir, requests)
        _write_cache_file(tempDir, now)

        (count, size) = _systemlink_storeandforward_inspector.calculate_pending_request_size(tempDir)

        assert count == 1
        assert size > 0


def test_emptyDirectory_calculatePendingRequests_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        result = _systemlink_storeandforward_inspector.calculate_pending_requests(tempDir)

        assert result == (0, 0)


def test_noCacheFile_calculatePendingRequests_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        _write_sample_transaction_buffer(tempDir, [(datetime.today(), "ResultCreateRequest")])

        result = _systemlink_storeandforward_inspector.calculate_pending_requests(tempDir)

        assert result == (0, 0)


def test_onlyAlreadyProcessedRequests_calculatePendingRequests_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        now = datetime.now()
        requests = [
            (now - timedelta(minutes=3), "ResultCreateRequest"),
            (now - timedelta(minutes=2), "ResultUpdateRequest"),
            (now - timedelta(minutes=1), "ResultUpdateRequest"),
        ]
        _write_sample_transaction_buffer(tempDir, requests)
        _write_cache_file(tempDir, now)

        result = _systemlink_storeandforward_inspector.calculate_pending_requests(tempDir)

        assert result == (0, 0)


def test_mixOfProcessedAndPendingRequests_calculatePendingRequests_returnsPending():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        now = datetime.now()
        request1 = [
            (now - timedelta(minutes=1), "ResultCreateRequest"),
            (now + timedelta(minutes=1), "ResultUpdateRequest"),
            (now + timedelta(minutes=2), "ResultUpdateRequest"),
        ]
        request2 = [
            (now - timedelta(minutes=6), "ResultCreateRequest"),
            (now - timedelta(minutes=5), "ResultUpdateRequest"),
            (now - timedelta(minutes=4), "ResultUpdateRequest"),
        ]
        request3 = [
            (now + timedelta(minutes=4), "StepCreateRequest"),
            (now + timedelta(minutes=5), "StepUpdateRequest"),
            (now + timedelta(minutes=6), "StepUpdateRequest"),
        ]
        _write_sample_transaction_buffer(tempDir, request1)
        _write_sample_transaction_buffer(tempDir, request2)
        _write_sample_transaction_buffer(tempDir, request3)
        _write_cache_file(tempDir, now)

        result = _systemlink_storeandforward_inspector.calculate_pending_requests(tempDir)

        assert result == (2, 3)


def test_realRequestTransactionsBuffer_calculatePendingRequests_returnsPending():
    storeDirectory = os.path.join(os.path.dirname(__file__), "testmon")
    result = _systemlink_storeandforward_inspector.calculate_pending_requests(storeDirectory)

    assert result == (3, 26)


def test_missingQuarantineDirectory_calculateQuaratineSize_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        result = _systemlink_storeandforward_inspector.calculate_quaratine_size(tempDir)

        assert result == (0, 0)


def test_emptyQuarantineDirectory_calculateQuaratineSize_returnsZero():
    with tempfile.TemporaryDirectory(prefix="test_") as tempDir:
        os.mkdir(os.path.join(tempDir, "quarantine"))
        result = _systemlink_storeandforward_inspector.calculate_quaratine_size(tempDir)

        assert result == (0, 0)


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
        requests1 = [
            (now - timedelta(minutes=1), "ResultCreateRequest"),
            (now + timedelta(minutes=1), "ResultUpdateRequest"),
            (now + timedelta(minutes=2), "ResultUpdateRequest"),
        ]
        request2 = [
            (now - timedelta(minutes=6), "ResultCreateRequest"),
            (now - timedelta(minutes=5), "ResultUpdateRequest"),
            (now - timedelta(minutes=4), "ResultUpdateRequest"),
        ]
        request3 = [
            (now + timedelta(minutes=4), "StepCreateRequest"),
            (now + timedelta(minutes=5), "StepUpdateRequest"),
            (now + timedelta(minutes=6), "StepUpdateRequest"),
        ]
        _write_sample_transaction_buffer(quarantineDirectory, requests1)
        _write_sample_transaction_buffer(quarantineDirectory, request2)
        _write_sample_transaction_buffer(quarantineDirectory, request3)

        result = _systemlink_storeandforward_inspector.calculate_quaratine_requests(tempDir)

        assert result == 9


def test_realRequestTransactionsBuffer_calculateQuaratineRequests_returnsQuarantined():
    storeDirectory = os.path.join(os.path.dirname(__file__), "testmon")
    result = _systemlink_storeandforward_inspector.calculate_quaratine_requests(storeDirectory)

    assert result == 62


def _write_sample_pending_file(directory: str):
    filename = str(uuid.uuid1()) + ".file"
    with open(os.path.join(directory, filename), "x") as fp:
        fp.write("empty")


def _write_sample_transaction_buffer(directory: str, requests: List[Tuple[datetime, str]]):
    lines = map(
        lambda tuple: json.dumps({"timestamp": datetime.isoformat(tuple[0]), "type": tuple[1]}, indent=None) + "\n",
        requests,
    )
    filename = str(uuid.uuid1()) + ".jsonl"
    with open(os.path.join(directory, filename), "x") as fp:
        fp.writelines(lines)


def _write_cache_file(directory: str, timestamp: datetime):
    contents = json.dumps({"timestamp": datetime.isoformat(timestamp)}, indent=None)
    with open(os.path.join(directory, "__CACHE__"), "x") as fp:
        fp.write(contents)
