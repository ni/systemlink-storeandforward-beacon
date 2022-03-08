# systemlink-storeandforward-beacon

SystemLink Store and Forward Beacon is a SaltStack beacon for monitoring
the health of the SystemLink Client store and forward feature. The beacon
will monitor folders involved with the operation of store and forward
to determine how many requests are pending to be forwarded, and how many
requests have been quarantined due to errors reported from requests to 
the server.

## Installation and configuration

1. Copy .py and .conf files to your server's salt root (C:\ProgramData\National Instruments\salt\srv\salt)
2. Import .sls file as a new state in the SystemLink States web UI
3. Apply the state to the systems you'd like to monitor
4. Restart the minions
5. Verify the tags appear in the SystemLink Tags web UI

## Development

`systemlink-storeandforward-beacon` uses the standard NI set of tools for development. See [the wiki](https://ni.visualstudio.com/DevCentral/_wiki/wikis/AppCentral.wiki/17456/Making-a-change-to-an-existing-project)
for information on how to contribute changes.