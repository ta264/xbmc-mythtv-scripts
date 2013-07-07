#!/bin/bash
# /etc/acpi/powerbtn.sh
# When power button is pressed, check if mythtv is busy before allowing shutdown

STATUS=$(mythshutdownstatus)
if [ $STATUS -eq 0 ]; then
    /etc/acpi/powerbtn.sh.orig
fi
