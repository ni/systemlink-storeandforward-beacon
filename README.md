# systemlink-storeandforward-beacon

SystemLink Store and Forward Beacon is a SaltStack beacon for monitoring
the health of the SystemLink Client store and forward feature. The beacon
will monitor folders involved with the operation of store and forward
to determine how many requests are pending to be forwarded, and how many
requests have been quarantined due to errors reported from requests to 
the server.

## Installation and configuration

1. Copy the `src/systemlink_storeandforward_beacon` directory and and `salt/systemlink_storeandforward_monitor.conf` file
   to your server's salt root
   - Defaults to `C:\ProgramData\National Instruments\salt\srv\salt`
2. Import `salt/systemlink_storeandforward_beacon.sls` file as a new state in the SystemLink States web UI
   - Open **System Management** > **States** from the navigation menu
   - Click the **Import** button in the toolbar
   - Browse to the .sls file
3. [Apply the state](https://www.ni.com/documentation/en/systemlink/latest/deployment/deploying-system-states/) to the systems you'd like to monitor
4. Verify the tags appear in the SystemLink Tag Viewer web UI. See [the SystemLink manual](https://www.ni.com/documentation/en/systemlink/latest/data/troubleshooting-tag-data/) for details.
   - The tags will have the path `<minion_id>.TestMonitor.StoreAndForward.*`
5. Create [Alarms](https://www.ni.com/documentation/en/systemlink/latest/manager/monitoring-system-health/) to
   be notified when the tags exceed limits for your application

## Development

`systemlink-storeandforward-beacon` uses [poetry](https://python-poetry.org/) to manage dependencies 
and Python version 3.6.8, which matches the version of Python included on SystemLink Client installations.