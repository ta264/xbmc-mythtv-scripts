#!/bin/bash
# /etc/acpi/powerbtn.sh
# When power button is pressed, check if mythtv is busy before allowing shutdown

logger "power button pressed, killing Kodi and restarting lightdm"
killall -SIGKILL kodi.bin
service lightdm restart
logger "lightdm restarted"
