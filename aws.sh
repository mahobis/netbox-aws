#!/bin/bash

echo  $'[default]\nregion = eu-central-1' > /root/.aws/config
/usr/bin/python3 /opt/scripts/aws-sync.py
#&>/dev/null &
echo $'[default]\nregion = eu-central-2' > /root/.aws/config
/usr/bin/python3 /opt/scripts/aws-sync.py
#&>/dev/null &
