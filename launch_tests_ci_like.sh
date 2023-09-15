#!/bin/bash

ARTIFACT_DIR="artifacts_coverages"
EXECUTOR="poetry run coverage"

PACKAGES="agent_toolkit datasource_sqlalchemy datasource_toolkit flask_agent"
# PACKAGES="datasource_toolkit"
PYTHON_VERSIONS="3.8 3.9 3.10 3.11"
# PYTHON_VERSIONS="3.8 3.11"

eval "$(pyenv init -)"
mkdir -p $ARTIFACT_DIR

# /!\ remove all coverage file command:
# /!\ find . | grep -i coverage | grep -v venv | grep -v .github | grep -v .coveragerc | xargs rm

cd src
rm -rf tmp_venv
echo "STARTING SCRIPT"
for package in $PACKAGES
do
    for py_version in $PYTHON_VERSIONS
    do
        cd $package

        echo "# --- # testing $package with python $py_version"
        pyenv shell $py_version  # use python desired version

        echo "# installing depencies"
        python -m venv ../tmp_venv  # create virtualenv
        source ../tmp_venv/bin/activate  # activate it
        rm -f poetry.lock  # theoricaly useless
        poetry install --with=test -q  # install requirements (-q: quiet)

        echo "# running tests"
        $EXECUTOR run -m pytest  # run tests

        deactivate  # deactivate venv
        rm -rf ../tmp_venv  # remove venv
        unset PYENV_VERSION  # unset python desired version

        mkdir -p ../../$ARTIFACT_DIR/$package-py_$py_version  # create coverage files directory (if no exists)
        mv .coverage ../../$ARTIFACT_DIR/$package-py_$py_version  # mv coverage file to it
        rm -f poetry.lock # theoricaly useless

        cd ..
    done
done

# combine coverage files, and generate xml report
poetry -C datasource_sqlalchemy run coverage combine ../$ARTIFACT_DIR/*/.coverage
poetry -C datasource_sqlalchemy run coverage xml
# poetry -C datasource_sqlalchemy run coverage html

# mv htmlcov ../
mv coverage.xml ../
mv .coverage ../

cd ..
rm -rf $ARTIFACT_DIR
poetry -C src/datasource_sqlalchemy run coverage report | tail -1