#!/bin/sh
# set -x

# api.development.forestadmin.com as host machine
if ! grep -q api.development.forestadmin.com /etc/hosts
then
    FOREST_BE=$(ping -c 1 host.docker.internal | awk 'NR==1 {print $3}' | cut -d \( -f2 | cut -d \) -f1)
    echo "$FOREST_BE   api.development.forestadmin.com" >> /etc/hosts
fi

# install requirements
echo "updating requirements"
/opt/poetry/bin/poetry install --no-cache -q

# init and seed db
if [ ! -f django_demo/db.sqlite3 ]
then
    echo "creating and seeding databases"
    /opt/poetry/bin/poetry run poe init-db
    /opt/poetry/bin/poetry run poe populate-db
fi

# set of command
# start long running process at the end that is passed from CMD
exec "$@"
