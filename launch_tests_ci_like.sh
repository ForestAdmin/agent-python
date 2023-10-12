#!/bin/bash
# set -x
ARTIFACT_DIR="artifacts_coverages"

PACKAGES="agent_toolkit datasource_sqlalchemy datasource_toolkit flask_agent"
# PACKAGES="flask_agent"
PYTHON_VERSIONS="3.8 3.9 3.10 3.11"
# PYTHON_VERSIONS="3.8 3.11"
# PYTHON_VERSIONS="3.11"

# flask related settings
# https://pypi.org/project/Flask/#history
FLASK_VERSIONS=(  # flask_version,(werkzeug_version:optional)
    "2.0.0" "2.0.1" "2.0.2" "2.0.3"
    "2.1.0" "2.1.1" "2.1.2" "2.1.3,2.1.2"
    "2.2.0" "2.2.1" "2.2.2" "2.2.3" "2.2.3" "2.2.4,2.2.3" "2.2.5,2.2.3"
    "2.3.0" "2.3.1" "2.3.2,2.3.3" "2.3.3,2.3.7"
    "3.0.0"
)

# sqlalchemy related settings
# https://pypi.org/project/SQLAlchemy/#history
version_number=0
for sub_version in {0..49}; do
    if [[ ! $sub_version =~ (^33|34$) ]]; then
        SQLALCHEMY_VERSIONS[$version_number]="1.4.$sub_version"
        let "version_number += 1"
    fi
done
for sub_version in {0..21}; do
    if [[ ! $sub_version =~ (^5$) ]]; then
        SQLALCHEMY_VERSIONS[$version_number]="2.0.$sub_version"
        let "version_number += 1"
    fi
done

# launch test on all versions only if we test 1 package
if [[ ${#PACKAGES[@]} == 1 ]]; then
    LAUNCH_ALL_FLASK_VERSIONS=true
    LAUNCH_ALL_SQLALCHEMY_VERSIONS=true
else
    LAUNCH_ALL_FLASK_VERSIONS=false
    LAUNCH_ALL_SQLALCHEMY_VERSIONS=false
fi
# LAUNCH_ALL_FLASK_VERSIONS=true
# LAUNCH_ALL_SQLALCHEMY_VERSIONS=true


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
        poetry install --with=test -q # install requirements (-q quiet)

        if [[ "$package" == "datasource_sqlalchemy" &&  $LAUNCH_ALL_FLASK_VERSIONS == true ]]
        then
            for versions in ${FLASK_VERSIONS[*]}
            do
                OLDIFS=$IFS
                IFS=','
                set -- $versions

                pip install -U flask==$1 werkzeug==${2:-$1}
                echo "#--------- running tests with flask==$1 werkzeug==${2:-$1}"
                $(which poetry) run coverage run -m pytest  # run tests

                IFS=$OLDIFS
            done
        elif [[ "$package" == "flask_agent" &&  $LAUNCH_ALL_SQLALCHEMY_VERSIONS == true ]]
        then
            for versions in ${SQLALCHEMY_VERSIONS[*]}
            do
                pip install -U sqlalchemy==$version
                echo "#--------- running tests with sqlalchemy==${versions}"
                $(which poetry) run coverage run -m pytest  # run tests
            done

        else
            echo "# running tests"
            $(which poetry) run coverage run -m pytest  # run tests
        fi

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
du -sh ../$ARTIFACT_DIR/
poetry -C datasource_sqlalchemy run coverage combine ../$ARTIFACT_DIR/*/.coverage
poetry -C datasource_sqlalchemy run coverage xml
# poetry -C datasource_sqlalchemy run coverage html

# mv htmlcov ../
mv coverage.xml ../
mv .coverage ../

cd ..
rm -rf $ARTIFACT_DIR
poetry -C src/datasource_sqlalchemy run coverage report | tail -1