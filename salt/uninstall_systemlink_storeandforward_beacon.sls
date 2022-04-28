remove_systemlink_storeandforward_monitor.py:
  file.absent:
    - name: 'C:\ProgramData\National Instruments\salt\var\extmods\beacons\systemlink_storeandforward_monitor.py'

remove_systemlink_storeandforward_inspector:
  file.absent:
    - name: 'C:\ProgramData\National Instruments\salt\var\extmods\beacons\_systemlink_storeandforward_inspector.py'

remove_systemlink_storeandforward_monitor.conf:
  file.absent:
    - name: 'C:\ProgramData\National Instruments\salt\conf\minion.d\systemlink_storeandforward_monitor.conf'

restart_saltminion:
  cmd.run:
    - name: "start -WindowStyle Hidden powershell { Start-Sleep -s 20; Restart-Service nisaltminion -Force }"
    - shell: powershell
