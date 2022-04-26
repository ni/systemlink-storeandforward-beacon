from datetime import datetime
import math
from typing import Dict, Tuple
import dateutil.parser
import glob
import json
import os


_result_transactions = ["ResultCreateRequest", "ResultUpdateRequest"]
_step_transactions = ["StepCreateRequest", "StepUpdateRequest"]


def calculate_pending_files(storeDirectory: str) -> int:
    """
    Calculate the pending files to be forwarded in the store and forward directory.

    :param storeDirectory: The data directory store and forward files are stored in.
    :return: The number of pending files to be uploaded
    """
    if not os.path.isdir(storeDirectory):
        return 0

    return len(glob.glob(os.path.join(storeDirectory, "*.file")))


def calculate_pending_request_size(storeDirectory: str) -> Tuple[int, int]:
    """
    Calculate the size of the pending request directory, in files and KiBytes

    :param storeDirectory: The data directory store and forward requests are stored in.
    :return: A tuple with the first value the number of request buffer files and the
      second value the size of the request buffers files in KiB
    """
    if not os.path.isdir(storeDirectory):
        return (0, 0)

    transactionBufferPaths = glob.glob(os.path.join(storeDirectory, "*.jsonl"))
    sizeInKiB = _sum_size_of_files_kib(transactionBufferPaths)
    return (len(transactionBufferPaths), sizeInKiB)


def calculate_pending_requests(storeDirectory: str) -> Tuple[int, int]:
    """
    Calculate the pending requests to be forwarded in the store and forward directory.

    :param storeDirectory: The data directory store and forward requests are stored in.
    :return: A tuple with the first value the number of pending results requests and the
      second value the number of pending steps requests
    """
    if not os.path.isdir(storeDirectory):
        return (0, 0)

    cacheFilePath = os.path.join(storeDirectory, "__CACHE__")
    if not os.path.isfile(cacheFilePath):
        return (0, 0)

    lastProcessedTimestamp = _read_last_processed_timestamp(cacheFilePath)
    pendingResults = 0
    pendingSteps = 0
    transactionBufferPaths = glob.glob(os.path.join(storeDirectory, "*.jsonl"))
    for transactionBufferPath in transactionBufferPaths:
        transactionCounts = _count_transactions_after(transactionBufferPath, lastProcessedTimestamp)
        for t in _result_transactions:
            pendingResults += transactionCounts.get(t, 0)
        for t in _step_transactions:
            pendingSteps += transactionCounts.get(t, 0)

    return (pendingResults, pendingSteps)


def calculate_quaratine_size(storeDirectory: str) -> Tuple[int, int]:
    """
    Calculate the size of the quaratine directory, in files and KiBytes

    :param storeDirectory: The data directory store and forward requests are stored in.
    :return: A tuple with the first value the number of request buffer files and the
      second value the size of the request buffers files in KiB
    """
    if not os.path.isdir(storeDirectory):
        return (0, 0)

    quaratineDirectory = os.path.join(storeDirectory, "quarantine")
    if not os.path.isdir(quaratineDirectory):
        return (0, 0)

    transactionBufferPaths = glob.glob(os.path.join(quaratineDirectory, "*.jsonl"))
    sizeInKiB = _sum_size_of_files_kib(transactionBufferPaths)
    return (len(transactionBufferPaths), sizeInKiB)


def calculate_quaratine_requests(storeDirectory: str) -> int:
    """
    Calculate the number of requests placed into quarantine.

    :param storeDirectory: The data directory store and forward requests are stored in.
    :return: The quantity of requests moved to quarantine.
    """
    if not os.path.isdir(storeDirectory):
        return 0

    quaratineDirectory = os.path.join(storeDirectory, "quarantine")
    if not os.path.isdir(quaratineDirectory):
        return 0

    quarantined = 0
    transactionBufferPaths = glob.glob(os.path.join(quaratineDirectory, "*.jsonl"))
    for transactionBufferPath in transactionBufferPaths:
        quarantined += len(list(_load_transactions(transactionBufferPath)))

    return quarantined


def _read_last_processed_timestamp(cacheFilePath: str) -> datetime:
    with open(cacheFilePath, "r", encoding="ansi") as cacheFile:
        cacheFileJson = json.load(cacheFile)
        return dateutil.parser.isoparse(cacheFileJson["timestamp"])


def _count_transactions_after(transactionBufferPath: str, lastProcessedTimestamp: datetime) -> Dict[str, int]:
    transactions = _load_transactions(transactionBufferPath)
    newTransactions = filter(lambda t: lastProcessedTimestamp <= dateutil.parser.isoparse(t["timestamp"]), transactions)
    transactionCounts: Dict[str, int] = {}
    for t in newTransactions:
        transactionCounts[t["type"]] = transactionCounts.get(t["type"], 0) + 1
    return transactionCounts


def _load_transactions(transactionBufferPath: str):
    lines = []
    with open(transactionBufferPath, "r", encoding="ansi") as transactionBuffer:
        lines = transactionBuffer.readlines()

    return map(lambda line: json.loads(line), lines)


def _sum_size_of_files_kib(transactionBufferPaths) -> int:
    if len(transactionBufferPaths) == 0:
        return 0

    return int(math.ceil(sum(os.path.getsize(f) for f in transactionBufferPaths if os.path.isfile(f)) / 1024))
