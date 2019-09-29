#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "installing dependencies"
#pip install -r requirements.txt --user

echo $DIR

if [[ -z "${ZWO_ASI_LIB}" ]]; then
  echo "Setting up ZWO_ASI_LIB env var in user env"
  bashrc_line="export ZWO_ASI_LIB=${DIR}/lib/libASICamera2.so.1.14.0715"
  echo $bashrc_line >> ~/.bashrc
else
  echo "ZWO_ASI_LIB env already set"
fi

sudo install lib/asi.rules /lib/udev/rules.d

echo "Creating startup entry"


echo "***************************"
echo "*  INSTALLATION COMPLETE  *"
echo "*                         *"
echo "*     PLEASE REBOOT!!     *"
echo "***************************"

