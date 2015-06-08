#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}


if [[ -z "$1" || -z "$2" ]]; then
    echo "usage $0 redirect_user redirect_password"
    exit 1
fi

./docker.sh

apt-get install sshpass
#ssh-keygen -f "/root/.ssh/known_hosts" -R [localhost]:2222

sshpass -p "syncloud" ssh -o StrictHostKeyChecking=no root@localhost -p 2222 "/test/integration/unit-test.sh"
sshpass -p "syncloud" ssh -o StrictHostKeyChecking=no root@localhost -p 2222 "/test/integration/pip-install.sh"
sshpass -p "syncloud" ssh -o StrictHostKeyChecking=no root@localhost -p 2222 "/test/integration/binary-install.py"
sshpass -p "syncloud" ssh -o StrictHostKeyChecking=no root@localhost -p 2222 "TEAMCITY_VERSION=\"$TEAMCITY_VERSION\" ;py.test -s /test/integration/verify.py --email=$1 --password=$2"