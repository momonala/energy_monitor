# Energy Monitor


### Setup SystemD services
`/lib/systemd/system/projects_energy_monitor.service`
```
[Unit]
 Description=Energy Monitor Service
 After=multi-user.target

 [Service]
 WorkingDirectory=/home/mnalavadi/energy_monitor 
 Type=idle
 ExecStart=/usr/local/bin/python3.10 fetch_data.py
 User=mnalavadi

 [Install]
 WantedBy=multi-user.target
```

`/lib/systemd/system/projects_energy_monitor_site.service`
```
[Unit]
 Description=Energy Monitor Website Service
 After=multi-user.target

 [Service]
 WorkingDirectory=/home/mnalavadi/energy_monitor 
 Type=idle
 ExecStart=/usr/local/bin/python3.10 energy_monitor.py
 User=mnalavadi

 [Install]
 WantedBy=multi-user.target
```

#### Start the services
```
sudo chmod 644 /lib/systemd/system/projects_energy_monitor.service
sudo chmod 644 /lib/systemd/system/projects_energy_monitor_site.service

sudo systemctl daemon-reload
sudo systemctl daemon-reexec

sudo systemctl enable projects_energy_monitor.service
sudo systemctl enable projects_energy_monitor_site.service

sudo reboot
```

#### View logs
```
journalctl -u projects_energy_monitor.service
journalctl -u projects_energy_monitor_site.service
```

#### Sync ALL local with Raspberry Pi
```
rsync -avu . mnalavadi@192.168.0.183:energy_monitor
```

#### Sync DB Raspberry Pi with local
```
rsync -avu mnalavadi@192.168.0.183:energy_monitor/data/energy_data.db data/energy_monitor.db
```
