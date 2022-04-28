'C:\ProgramData\National Instruments\salt\var\extmods\beacons\systemlink_storeandforward_monitor.py':
  file.managed:
    - source: 'salt://systemlink_storeandforward_beacon/systemlink_storeandforward_monitor.py'

'C:\ProgramData\National Instruments\salt\var\extmods\beacons\_systemlink_storeandforward_inspector.py':
  file.managed:
    - source: 'salt://systemlink_storeandforward_beacon/_systemlink_storeandforward_inspector.py'

'C:\ProgramData\National Instruments\salt\conf\minion.d\systemlink_storeandforward_monitor.conf':
  file.managed:
    - source: 'salt://systemlink_storeandforward_monitor.conf'

restart_saltminion:
  cmd.run:
    - name: "start -WindowStyle Hidden powershell { Start-Sleep -s 20; Restart-Service nisaltminion -Force }"
    - shell: powershell
