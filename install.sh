#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ZWO_ASI_LIB_PATH="${DIR}/asilib/libASICamera2.so.1.14.0715"

echo "installing dependencies"
pip install -r requirements.txt --user

sed  "s|ZWOASILIB_PATH|$ZWO_ASI_LIB_PATH|g" allsky.cfg
echo "installing asi udev rules"
sudo install asilib/asi.rules /lib/udev/rules.d

echo "Creating startup entry"
echo "@reboot $DIR/allsky.py &" | crontab -u pi -

echo "***************************"
echo "*  INSTALLATION COMPLETE  *"
echo "*                         *"
echo "*     PLEASE REBOOT!!     *"
echo "***************************"

