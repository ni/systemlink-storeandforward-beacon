'C:\ProgramData\National Instruments\salt\var\extmods\beacons\systemlink_storeandforward_monitor.py':
  file.managed:
    - source: 'salt://systemlink_storeandforward_monitor.py'
    - makedirs: True

'C:\ProgramData\National Instruments\salt\conf\minion.d\systemlink_storeandforward_monitor.conf':
  file.managed:
    - source: 'salt://systemlink_storeandforward_monitor.conf'
    - makedirs: True

nisystemlink-clients:
  pip.installed:
    - name: nisystemlink-clients >= 0.1.3
