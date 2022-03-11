'C:\ProgramData\National Instruments\salt\var\extmods\beacons\systemlink_storeandforward_monitor.py':
  file.managed:
    - source: 'salt://systemlink_storeandforward_beacon/systemlink_storeandforward_monitor.py'

'C:\ProgramData\National Instruments\salt\var\extmods\beacons\_systemlink_storeandforward_inspector.py':
  file.managed:
    - source: 'salt://systemlink_storeandforward_beacon/_systemlink_storeandforward_inspector.py'

'C:\ProgramData\National Instruments\salt\conf\minion.d\systemlink_storeandforward_monitor.conf':
  file.managed:
    - source: 'salt://systemlink_storeandforward_monitor.conf'

nisystemlink-clients:
  pip.installed:
    - name: nisystemlink-clients >= 0.1.3

reboot:
  system.reboot:
    - message: 'System is rebooting now'
    - timeout: 10
    - in_seconds: true
    - only_on_pending_reboot: False