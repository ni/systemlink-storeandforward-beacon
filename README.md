# systemlink-storeandforward-beacon

SystemLink Store and Forward Beacon is a SaltStack beacon for monitoring
the health of the SystemLink Client store and forward feature. The beacon
will monitor folders involved with the operation of store and forward
to determine how many requests are pending to be forwarded, and how many
requests have been quarantined due to errors reported from requests to
the server.

This example has only been tested on Windows with a default installation
of SystemLink 2022 Q1 and is provided as is.

For more information see [Salt States](https://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html)
and [Salt Beacons](https://docs.saltproject.io/en/latest/topics/beacons/index.html).

## Installation

### Using NI Package (Recommended)

Requires NI Package Manager 20.0.0 or later on the client system.

1. [Upload](https://www.ni.com/docs/en-US/bundle/deploying-applications-clients-systemlink-2021-r2/page/enabling-client-access-to-packages.html) `ni-systemlink-storeandforward-beacon_<version>_windows_all.nipkg` to a feed in SystemLink Package Repository.
2. [Deploy](https://www.ni.com/docs/en-US/bundle/deploying-applications-clients-systemlink-2021-r2/page/deploying-packages.html) the **NI SystemLink Store and Forward Beacon** package to the client.

### Using SaltStack

1. Copy the `src/systemlink_storeandforward_beacon` directory and and `salt/systemlink_storeandforward_monitor.conf` file
   to your server's salt root
   - Defaults to `C:\ProgramData\National Instruments\salt\srv\salt`
2. Import `salt/systemlink_storeandforward_beacon.sls` file as a new state in the SystemLink States web UI
   - Open **System Management** > **States** from the navigation menu
   - Click the **Import** button in the toolbar
   - Browse to the .sls file
3. [Apply the state](https://www.ni.com/documentation/en/systemlink/latest/deployment/deploying-system-states/) to the systems you'd like to monitor

## Uninstallation

### Using NI Package

Use Systems Management to uninstall the **NI SystemLink Store and Forward Beacon** package from the client.

### Using SaltStack

Import `salt/uninstall_systemlink_storeandforward_beacon.sls` file as a new state and run it on the systems you wish to uninstall the beacon from.

## Configuration

1. Verify the tags appear in the SystemLink Tag Viewer web UI. See [the SystemLink manual](https://www.ni.com/documentation/en/systemlink/latest/data/troubleshooting-tag-data/) for details.
   - The tags will have the path `<minion_id>.TestMonitor.StoreAndForward.*`
2. Create [Alarms](https://www.ni.com/documentation/en/systemlink/latest/manager/monitoring-system-health/) to
   be notified when the tags exceed limits for your application

## Development

`systemlink-storeandforward-beacon` uses [poetry](https://python-poetry.org/)
to manage dependencies and Python version 3.6.8, which matches the version of
Python included on SystemLink Client 2022 Q1 installations.

The package can be built using [NI Package Builder 20.0.0](https://www.ni.com/en-us/support/downloads/software-products/download.ni-package-builder.html#367057).
Using a newer version of Package Builder will require an newer version of NI Package Manager on the client system.
