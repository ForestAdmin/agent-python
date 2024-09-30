#!/bin/bash
# set -x
ARTIFACT_DIR="artifacts_coverages"

PACKAGES=("agent_toolkit" "datasource_sqlalchemy" "datasource_toolkit" "flask_agent" "datasource_django" "django_agent")
# PACKAGES=("datasource_sqlalchemy")
PYTHON_VERSIONS=("3.8" "3.9" "3.10" "3.11" "3.12")
# PYTHON_VERSIONS=("3.8" "3.11")
PYTHON_VERSIONS=("3.12")

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
SQLALCHEMY_VERSIONS=()
for sub_version in {0..49}; do
    if [[ ! $sub_version =~ (^33|34$) ]]; then
        version="1.4.$sub_version"
        SQLALCHEMY_VERSIONS=(${SQLALCHEMY_VERSIONS[@]} $version)
    fi
done
for sub_version in {0..21}; do
    if [[ ! $sub_version =~ (^5$) ]]; then
        version="2.0.$sub_version"
        SQLALCHEMY_VERSIONS+=($version)
    fi
done
DJANGO_VERSIONS=("3.2" "4.0" "4.1" "4.2" "5.0")

# launch test on all versions only if we test 1 package
if [[ ${#PACKAGES[@]} == 1 ]]; then
    LAUNCH_ALL_FLASK_VERSIONS=true
    LAUNCH_ALL_SQLALCHEMY_VERSIONS=true
    LAUNCH_ALL_DJANGO_VERSIONS=true
else
    LAUNCH_ALL_FLASK_VERSIONS=false
    LAUNCH_ALL_SQLALCHEMY_VERSIONS=false
    LAUNCH_ALL_DJANGO_VERSIONS=false
fi

eval "$(pyenv init -)"
mkdir -p $ARTIFACT_DIR

# /!\ remove all coverage file command:
# /!\ find . | grep -i coverage | grep -v venv | grep -v .github | grep -v .coveragerc | xargs rm

cd src
rm -rf tmp_venv
echo "STARTING SCRIPT"
for package in ${PACKAGES[@]}
do
    for py_version in ${PYTHON_VERSIONS[@]}
    do
        cd $package

        echo "# --- # testing $package with python $py_version"
        pyenv shell $py_version  # use python desired version

        echo "# installing depencies"
        python -m venv ../tmp_venv  # create virtualenv
        source ../tmp_venv/bin/activate  # activate it
        rm -f poetry.lock  # theoricaly useless
        poetry install --with=test -q # install requirements (-q quiet)

        if [[ "$package" == "flask_agent" &&  $LAUNCH_ALL_FLASK_VERSIONS == true ]]
        then
            for versions in ${FLASK_VERSIONS[*]}
            do
                OLDIFS=$IFS
                IFS=','
                set -- $versions

                pip install -q -U flask==$1 werkzeug==${2:-$1}
                echo "#--------- running tests with flask==$1 werkzeug==${2:-$1}"
                $(which poetry) run coverage run -m pytest  # run tests

                IFS=$OLDIFS
            done
        elif [[ "$package" == "datasource_sqlalchemy" &&  $LAUNCH_ALL_SQLALCHEMY_VERSIONS == true ]]
        then
            # pip install -q -U flask==2.1.3 werkzeug==2.1.2 flask_sqlalchemy sqlalchemy==1.4.0
            for version in ${SQLALCHEMY_VERSIONS[@]}
            do
                if [[ ${version:0:1} == 1 ]]; then
                    pip install -q -U flask==2.1.3 werkzeug==2.1.2 flask_sqlalchemy sqlalchemy==$version
                elif [[ ${version:0:1} == 2 ]]; then
                    pip install -q -U flask werkzeug flask_sqlalchemy sqlalchemy==$version
                fi
                echo "#--------- running tests with sqlalchemy==$version"
                $(which poetry) run coverage run -m pytest  # run tests
            done
        elif [[ ("$package" == "datasource_django" || "$package" == "django_agent") &&  $LAUNCH_ALL_DJANGO_VERSIONS == true ]]
        then
            for version in ${DJANGO_VERSIONS[@]}
            do
                pip install -q -U django==$version
                echo "#--------- running tests with django==$version"
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