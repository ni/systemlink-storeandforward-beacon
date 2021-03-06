"""SystemLink TestMonitor store and forward health monitor beacon."""

import asyncio
import atexit
import logging
import os
import sys
from typing import Any, Dict, List, Tuple, Union
from urllib.parse import quote
import winreg
import psutil
from systemlink.clientconfig import get_configuration_by_id, HTTP_MASTER_CONFIGURATION_ID
from systemlink.clients.nitag import (
    ApiClient,
    ApiException,
    Tag,
    TagListAndMergeFlag,
    TagsApi,
    TagUpdate,
    TagValue,
    TimestampedTagValue,
)
from systemlink.clients.nitag.rest import RESTResponse

# Import local libs
# This file may be loaded out of __pycache__, so the
# directory of its .py may not be in the search path.
IMPORT_PATH = os.path.dirname(__file__)
if IMPORT_PATH.endswith("__pycache__"):
    IMPORT_PATH = os.path.dirname(IMPORT_PATH)
sys.path.append(IMPORT_PATH)
try:
    import _systemlink_storeandforward_inspector
finally:
    # Remove the extra search path that we added to sys.path
    sys.path.remove(IMPORT_PATH)

log = logging.getLogger(__name__)

NI_INSTALLERS_REG_PATH = "SOFTWARE\\National Instruments\\Common\\Installer"
NI_INSTALLERS_REG_KEY_APP_DATA = "NIPUBAPPDATADIR"

# The Python Event Loop for asynchronous actions
EVENT_LOOP: asyncio.AbstractEventLoop = None

# The client for the SystemLink Tags API
API_CLIENT: ApiClient = None
TAG_INFO: Dict[str, Dict[str, Any]] = {}

ATEXIT_REGISTERED = False
BEACON_INITIALIZED = False

__virtualname__: str = "systemlink_storeandforward_monitor"


def __virtual__() -> Union[str, Tuple[bool, str]]:
    """
    During module lazy loading, will return the virtual name of this module.

    :return: The virtual name of this module. On error, return a 2-tuple with
        ``False`` for the first item and the error message for the second.
    """
    return __virtualname__


def validate(config: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Validate the beacon configuration.

    :param config: The beacon configuration.
    :return: A 2-tuple. The first item is ``True`` if the
        configuration is valid and ``False`` otherwise. The second item
        is a message.
    """
    return True, "Valid beacon configuration"


def beacon(config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    SystemLink TestMonitor store and forward health monitor beacon.

    :param config: The beacon configuration.
    :return: A list of events to send to the master.
    """
    global BEACON_INITIALIZED

    try:
        if not BEACON_INITIALIZED:
            success = _init_beacon()
            if not success:
                return []
        EVENT_LOOP.run_until_complete(_update_fast_tag_values())
        EVENT_LOOP.run_until_complete(_update_slow_tag_values())
    except Exception as exc:
        log.error(
            'Unexpected exception in "systemlink_storeandforward_monitor beacon": %s',
            exc,
            exc_info=True,
        )

    # Always return an empty list so that nothing is sent to the master
    # via Salt mechanisms.
    return []


def _init_beacon() -> bool:
    global ATEXIT_REGISTERED
    global BEACON_INITIALIZED
    global EVENT_LOOP
    global API_CLIENT
    global TAG_INFO

    if BEACON_INITIALIZED:
        return True

    if not EVENT_LOOP:
        EVENT_LOOP = asyncio.get_event_loop()

    if API_CLIENT:
        # Always re-initialize the API_CLIENT in case the credentials or
        # certificate have changed.
        EVENT_LOOP.run_until_complete(API_CLIENT.close())
        API_CLIENT = None

    configuration = get_configuration_by_id(HTTP_MASTER_CONFIGURATION_ID, "/nitag", False)
    API_CLIENT = ApiClient(configuration=configuration)

    if not ATEXIT_REGISTERED:
        atexit.register(_cleanup_beacon)
        ATEXIT_REGISTERED = True

    minion_id = __grains__["id"]
    hostname = __grains__["host"]
    workspace = __grains__["systemlink_workspace"]
    retention = __grains__["health_monitoring_retention_type"].upper()
    historyTTLDays = str(__grains__["health_monitoring_retention_duration_days"])
    maxHistoryCount = str(__grains__["health_monitoring_retention_max_history_count"])
    log.debug(f"Creating beacon tags on {hostname} ({minion_id}) for workspace {workspace}")
    _setup_tags(TAG_INFO, minion_id)
    EVENT_LOOP.run_until_complete(
        _create_or_update_tag_metadata(minion_id, hostname, workspace, retention, historyTTLDays, maxHistoryCount)
    )

    BEACON_INITIALIZED = True
    return True


def _cleanup_beacon():
    global BEACON_INITIALIZED
    global API_CLIENT
    global EVENT_LOOP

    if API_CLIENT:
        # Disable logging when closing the Tag Client. _cleanup_beacon() is
        # called due to 'atexit.register', and this call can occur after the
        # logging process has exited. If the logging process has exited, and
        # it tries to log to the logging queue, the logging queue will block
        # waiting for send to flush (which will never happen since the
        # receiving process has exited), which will in turn hang this process
        # as it is trying to exit.
        logging.disable(logging.CRITICAL)
        EVENT_LOOP.run_until_complete(API_CLIENT.close())
        API_CLIENT = None
        logging.disable(logging.NOTSET)
    TAG_INFO.clear()
    BEACON_INITIALIZED = False


def _setup_tags(tag_info: Dict[str, Dict[str, str]], id: str):
    tag_info["service_status"] = {
        "path": id + ".TestMonitor.StoreAndForward.ServiceStatus",
        "type": "STRING",
        "displayName": "{} FORWARDING SERVICE STATUS",
        "fast": True,
    }
    tag_info["pending.results"] = {
        "path": id + ".TestMonitor.StoreAndForward.Pending.Results",
        "type": "DOUBLE",
        "displayName": "{} PENDING RESULT UPDATES TO SEND",
        "fast": False,
    }
    tag_info["pending.steps"] = {
        "path": id + ".TestMonitor.StoreAndForward.Pending.Steps",
        "type": "DOUBLE",
        "displayName": "{} PENDING STEP UPDATES TO SEND",
        "fast": False,
    }
    tag_info["pending.buffer_file_count"] = {
        "path": id + ".TestMonitor.StoreAndForward.Pending.BufferFileCount",
        "type": "DOUBLE",
        "displayName": "{} UPDATES BUFFER FILE COUNT",
        "fast": True,
    }
    tag_info["pending.buffer_file_size"] = {
        "path": id + ".TestMonitor.StoreAndForward.Pending.BufferFileSizeKiB",
        "type": "DOUBLE",
        "displayName": "{} UPDATES BUFFER FILE SIZE IN KiB",
        "fast": True,
    }
    tag_info["pending.files"] = {
        "path": id + ".TestMonitor.StoreAndForward.Pending.Files",
        "type": "DOUBLE",
        "displayName": "{} FILES PENDING UPLOAD",
        "fast": True,
    }
    tag_info["quarantine"] = {
        "path": id + ".TestMonitor.StoreAndForward.Quarantine",
        "type": "DOUBLE",
        "displayName": "{} REQUESTS IN QUARANTINE",
        "fast": False,
    }
    tag_info["quarantine.buffer_file_count"] = {
        "path": id + ".TestMonitor.StoreAndForward.Quarantine.BufferFileCount",
        "type": "DOUBLE",
        "displayName": "{} QUARANTINE FILE COUNT",
        "fast": True,
    }
    tag_info["quarantine.buffer_file_size"] = {
        "path": id + ".TestMonitor.StoreAndForward.Quarantine.BufferFileSizeKiB",
        "type": "DOUBLE",
        "displayName": "{} QUARANTINE FILE SIZE IN KiB",
        "fast": True,
    }


async def _create_or_update_tag_metadata(
    id: str,
    hostname: str,
    workspace: str,
    retention: str,
    historyTTLDays: str,
    maxHistoryCount: str,
):
    global API_CLIENT
    global TAG_INFO
    log.debug(f"Creating tag metadata for tags on {hostname} ({id}) for workspace {workspace}")
    tags = []
    for tag in TAG_INFO.values():
        properties = {
            "minionId": id,
            "displayName": tag["displayName"].format(hostname),
            "nitagRetention": retention,
            "nitagHistoryTTLDays": historyTTLDays,
            "nitagMaxHistoryCount": maxHistoryCount,
            "hyperLink": "#tagviewer/tag/" + quote(workspace, safe="") + "/" + quote(tag["path"], safe=""),
        }
        tags.append(Tag(type=tag["type"], properties=properties, path=tag["path"], collect_aggregates=True))
    tags_and_merge = TagListAndMergeFlag(tags, False)
    tags_api = TagsApi(api_client=API_CLIENT)
    response = await tags_api.create_or_update_tags(tags_and_merge, _preload_content=False)
    if response.status not in (200, 201, 202):
        data = await response.text()
        rest_response = RESTResponse(response, data)
        raise ApiException(http_resp=rest_response)


async def _update_fast_tag_values():
    global API_CLIENT
    global TAG_INFO
    _update_service_status()
    _calculate_forwarding_buffer_stats()
    _calculate_pending_files()
    updates = []
    for tag in TAG_INFO.values():
        if tag["fast"]:
            # A timestamp of ``None`` means use the server time.
            update = TimestampedTagValue(value=TagValue(value=str(tag["value"]), type=tag["type"]), timestamp=None)
            updates.append(TagUpdate(path=tag["path"], updates=[update]))

    tags_api = TagsApi(api_client=API_CLIENT)
    response = await tags_api.update_tag_current_values(updates, _preload_content=False)
    if response.status not in (200, 202):
        data = await response.text()
        rest_response = RESTResponse(response, data)
        raise ApiException(http_resp=rest_response)


async def _update_slow_tag_values():
    global API_CLIENT
    global TAG_INFO
    _calculate_pending_requests()
    _calculate_quarantine_requests()
    updates = []
    for tag in TAG_INFO.values():
        if not tag["fast"]:
            # A timestamp of ``None`` means use the server time.
            update = TimestampedTagValue(value=TagValue(value=str(tag["value"]), type=tag["type"]), timestamp=None)
            updates.append(TagUpdate(path=tag["path"], updates=[update]))

    tags_api = TagsApi(api_client=API_CLIENT)
    response = await tags_api.update_tag_current_values(updates, _preload_content=False)
    if response.status not in (200, 202):
        data = await response.text()
        rest_response = RESTResponse(response, data)
        raise ApiException(http_resp=rest_response)


def _update_service_status():
    global TAG_INFO
    TAG_INFO["service_status"]["value"] = "unknown"
    try:
        service = psutil.win_service_get("nisystemlinkforwarding")
        TAG_INFO["service_status"]["value"] = service.status()
    except psutil.NoSuchProcess:
        TAG_INFO["service_status"]["value"] = "missing"
    except Exception as ex:
        log.error("Failed to get nisystemlinkforwarding service information. " + str(ex))


def _calculate_forwarding_buffer_stats():
    global TAG_INFO
    storeDirectory = _get_testmon_store_directory()
    (
        pendingFileCount,
        pendingFileSize,
    ) = _systemlink_storeandforward_inspector.calculate_pending_request_size(storeDirectory)
    (
        quarantineFileCount,
        quarantineFileSize,
    ) = _systemlink_storeandforward_inspector.calculate_quaratine_size(storeDirectory)
    TAG_INFO["pending.buffer_file_count"]["value"] = pendingFileCount
    TAG_INFO["pending.buffer_file_size"]["value"] = pendingFileSize
    TAG_INFO["quarantine.buffer_file_count"]["value"] = quarantineFileCount
    TAG_INFO["quarantine.buffer_file_size"]["value"] = quarantineFileSize


def _calculate_pending_requests():
    global TAG_INFO
    storeDirectory = _get_testmon_store_directory()
    (
        pendingResults,
        pendingSteps,
    ) = _systemlink_storeandforward_inspector.calculate_pending_requests(storeDirectory)
    TAG_INFO["pending.results"]["value"] = pendingResults
    TAG_INFO["pending.steps"]["value"] = pendingSteps


def _calculate_quarantine_requests():
    global TAG_INFO
    storeDirectory = _get_testmon_store_directory()
    quarantined = _systemlink_storeandforward_inspector.calculate_quaratine_requests(storeDirectory)
    TAG_INFO["quarantine"]["value"] = quarantined


def _calculate_pending_files():
    global TAG_INFO
    storeDirectory = _get_files_store_directory()
    files = _systemlink_storeandforward_inspector.calculate_pending_files(storeDirectory)
    TAG_INFO["pending.files"]["value"] = files


def _get_testmon_store_directory() -> str:
    return os.path.join(_get_ni_common_appdata_dir(), "Skyline", "Data", "Store", "testmon")


def _get_files_store_directory() -> str:
    return os.path.join(_get_ni_common_appdata_dir(), "Skyline", "Data", "Store", "file")


def _get_ni_common_appdata_dir() -> str:
    r"""
    Return the National Instruments Common Application Data Directory.

    This looks like 'C:\ProgramData\National Instruments'
    :return: The National Instruments Common Application Data Directory.
    :rtype: str
    """
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, NI_INSTALLERS_REG_PATH, 0, winreg.KEY_READ) as hkey:
        (appdata_dir, _) = winreg.QueryValueEx(hkey, NI_INSTALLERS_REG_KEY_APP_DATA)
        return appdata_dir
