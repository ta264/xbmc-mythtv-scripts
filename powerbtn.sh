#!/bin/bash
# /etc/acpi/powerbtn.sh
# When power button is pressed, check if mythtv is busy before allowing shutdown

logger "power button pressed, killing Kodi and restarting"
service kodi restart
logger "kodi restarted"
