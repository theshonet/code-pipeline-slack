#!/bin/bash -e

# package.sh
# Installs dependendies into target folder and create lambda zip package
#

echo "Installing dependencies into ${TARGET_FOLDER} ... "
pipenv run pip install -r <(pipenv lock -r) --target ${TARGET_FOLDER}
cp ./src/* ${TARGET_FOLDER}
rm -f ${ZIP_FILE}

pushd ${TARGET_FOLDER}
zip -r ../${ZIP_FILE} .
popd

rm -rf ${TARGET_FOLDER}
