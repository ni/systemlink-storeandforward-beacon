"""SystemLink TestMonitor store and forward health monitor beacon."""

import asyncio
import json
import logging
import os
import random
from typing import Any, Dict, List, Tuple, Union
from urllib.parse import quote
import winreg
from systemlink.clients.core import HttpConfiguration
from systemlink.clients.tag import DataType, TagData, TagManager

log = logging.getLogger(__name__)

NI_INSTALLERS_REG_PATH = "SOFTWARE\\National Instruments\\Common\\Installer"
NI_INSTALLERS_REG_KEY_APP_DATA = "NIPUBAPPDATADIR"

# The Python Event Loop for asynchronous actions
EVENT_LOOP: asyncio.AbstractEventLoop = None

# The manager for the SystemLink Tags API
TAG_MANAGER: TagManager = None
TAG_INFO: Dict[str, Dict[str, Any]] = {}

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
        EVENT_LOOP.run_until_complete(_update_tag_values())
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
    global BEACON_INITIALIZED
    global EVENT_LOOP
    global TAG_MANAGER
    global TAG_INFO

    if BEACON_INITIALIZED:
        return True

    if not EVENT_LOOP:
        EVENT_LOOP = asyncio.get_event_loop()

    configuration = _get_http_configuration()
    TAG_MANAGER = TagManager(configuration)

    minion_id = __grains__["id"]
    hostname = __grains__["host"]
    workspace = __grains__["systemlink_workspace"]
    log.debug(f"Creating beacon tags on {hostname} ({minion_id}) for workspace {workspace}")
    _setup_tags(TAG_INFO, minion_id)
    EVENT_LOOP.run_until_complete(_create_or_update_tag_metadata(minion_id, hostname, workspace))

    BEACON_INITIALIZED = True
    return True


def _setup_tags(tag_info: Dict[str, Dict[str, DataType]], id: str):
    tag_info["pending"] = {
        "path": id + ".TestMonitor.StoreAndForward.Pending",
        "dataType": DataType.DOUBLE,
        "displayName": "{} PENDING REQUESTS TO SEND",
    }
    tag_info["quarantine"] = {
        "path": id + ".TestMonitor.StoreAndForward.Quarantine",
        "dataType": DataType.DOUBLE,
        "displayName": "{} REQUESTS IN QUARANTINE",
    }


async def _create_or_update_tag_metadata(id: str, hostname: str, workspace: str):
    global TAG_MANAGER
    global TAG_INFO
    log.debug(f"Creating tag metadata for tags on {hostname} ({id}) for workspace {workspace}")
    tags = []
    for tag in TAG_INFO.values():
        properties = {
            "minionId": id,
            "displayName": tag["displayName"].format(hostname),
            "hyperLink": "#tagviewer/tag/"
            + quote(workspace, safe="")
            + "/"
            + quote(tag["path"], safe=""),
        }
        tags.append(TagData(data_type=tag["dataType"], path=tag["path"], properties=properties))
    await TAG_MANAGER.update_async(tags)


async def _update_tag_values():
    global TAG_MANAGER
    global TAG_INFO
    _calculate_pending_requests()
    _calculate_quarantine_requests()
    with TAG_MANAGER.create_writer(buffer_size=len(TAG_INFO)) as writer:
        for tag in TAG_INFO.values():
            log.debug("Writing tags for beacon on " + tag["path"])
            await writer.write_async(tag["path"], tag["dataType"], tag["value"])


def _calculate_pending_requests():
    TAG_INFO["pending"]["value"] = random.randint(1, 100)


def _calculate_quarantine_requests():
    TAG_INFO["quarantine"]["value"] = random.randint(1, 100)


def _get_http_configuration() -> HttpConfiguration:
    httpConfigPath = _get_http_master_file()
    log.debug("Loading HTTP configuration from " + httpConfigPath)
    with open(httpConfigPath, "r") as httpConfigFile:
        httpConfigJson = json.load(httpConfigFile)
        return HttpConfiguration(
            server_uri=httpConfigJson["Uri"],
            api_key=httpConfigJson["ApiKey"],
            cert_path=httpConfigJson["CertPath"],
        )


def _get_http_master_file() -> str:
    """
    Return path to the Master HTTP credentials file on the minion.

    @return: Path to Master HTTP credentials file
    @rtype: str
    """
    file_path = _get_ni_common_appdata_dir()
    file_path = os.path.join(file_path, "Skyline", "HttpConfigurations", "http_master.json")
    return file_path


def _get_ni_common_appdata_dir() -> str:
    r"""
    Return the National Instruments Common Application Data Directory.

    This looks like 'C:\ProgramData\National Instruments'
    :return: The National Instruments Common Application Data Directory.
    :rtype: str
    """
    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE, NI_INSTALLERS_REG_PATH, 0, winreg.KEY_READ
    ) as hkey:
        (appdata_dir, _) = winreg.QueryValueEx(hkey, NI_INSTALLERS_REG_KEY_APP_DATA)
        return appdata_dir
