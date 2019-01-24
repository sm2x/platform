#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}
NAME="platform"
BUILD_DIR=${DIR}/build/${NAME}

${BUILD_DIR}/python/bin/pip install -r ${DIR}/dev_requirements.txt

cd ${DIR}/src
${BUILD_DIR}/python/bin/py.test.sh test