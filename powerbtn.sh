#!/bin/bash
# /etc/acpi/powerbtn.sh
# When power button is pressed, check if mythtv is busy before allowing shutdown

logger "power button pressed"

# run as 'tom' else mythshutdown will barf
su tom -c "checkshutdown"
status=$?
logger "status is $status"

if [ $status -eq 0 ]; then
    logger "shutdown allowed"
    poweroff
else
    logger "shutdown is not allowed"
fi
