#!/bin/bash -e

# package.sh
# Installs dependendies into target folder and create lambda zip package
# 


set -a
. ./.env
set +a

echo "Installing dependencies into ${TARGET_FOLDER} ... "
pipenv run pip install -r <(pipenv lock -r) --target ${TARGET_FOLDER}
cp ./src/* ${TARGET_FOLDER}
rm -f ${ZIP_FILE}

pushd ${TARGET_FOLDER}
zip -r ../${ZIP_FILE} .
popd

rm -rf ${TARGET_FOLDER}

parameters=$(cat .env)
capabilities="CAPABILITY_NAMED_IAM"

echo "Packaging AWS SAM Application"
	sam package \
		--template-file ${TEMPLATE_NAME} \
		--s3-bucket ${BUCKET_NAME} \
		--output-template-file packaged-${TEMPLATE_NAME} \
		--profile ${PROFILE}
	
	echo "Deploying AWS SAM Application"
	sam deploy \
		--template-file packaged-${TEMPLATE_NAME} \
		--stack-name ${STACK_NAME} \
		--capabilities ${capabilities} \
		--profile ${PROFILE} \
		--parameter-overrides ${parameters}
