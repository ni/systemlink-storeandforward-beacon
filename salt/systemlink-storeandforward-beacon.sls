'C:\ProgramData\National Instruments\salt\var\extmods\beacons\systemlink_storeandforward_monitor.py':
  file.managed:
    - source: 'salt://systemlink_storeandforward_monitor.py'
    - makedirs: True

'C:\ProgramData\National Instruments\salt\var\extmods\beacons\_systemlink_storeandforward_inspector.py':
  file.managed:
    - source: 'salt://_systemlink_storeandforward_inspector.py'
    - makedirs: True

'C:\ProgramData\National Instruments\salt\conf\minion.d\systemlink_storeandforward_monitor.conf':
  file.managed:
    - source: 'salt://systemlink_storeandforward_monitor.conf'
    - makedirs: True

nisystemlink-clients:
  pip.installed:
    - name: nisystemlink-clients >= 0.1.3, <=1

python-dateutil:
  pip.installed:
    - name: nisystemlink-clients >= 2.8.2, <=3
