#!/bin/bash -e
# install dependendies into target folder and create lambda zip package

# build folder
TARGET_FOLDER=./target
ZIP_FILE=./lambda.zip
AWS_PROFILE=$1
AWS_REGION=$2
S3_BUCKET="${AWS_PROFILE}-cloudformation-artifacts-1"
PROJECT_NAME=code-pipeline-slack


if [[ -z ${AWS_PROFILE} ]]
then
  echo "An AWS profile is needed"
  echo "$1 <profile> <region>"
  exit 1
fi

if [[ -z ${AWS_REGION} ]]
then
  echo "An AWS region is needed"
  echo "$1 <profile> <region>"
  exit 1
fi
echo "Installing dependencies into ${TARGET_FOLDER} ... "
pipenv run pip install -r <(pipenv lock -r) --target ${TARGET_FOLDER}
cp ./src/* ${TARGET_FOLDER}
rm -f ${ZIP_FILE}
pushd ${TARGET_FOLDER}
zip -r ../${ZIP_FILE} .
popd
rm -rf ${TARGET_FOLDER}

# upload zip package + template
echo "Uploading to s3://${S3_BUCKET} ${PROJECT_NAME}"
aws s3 mb --profile=${AWS_PROFILE}  --region=${AWS_REGION} s3://${S3_BUCKET}
aws cloudformation package --profile=${AWS_PROFILE} --region=${AWS_REGION} --template-file ./template.yml --s3-bucket ${S3_BUCKET} --s3-prefix ${PROJECT_NAME} --output-template-file packaged-template.yml
aws s3 --profile=${AWS_PROFILE} --region=${AWS_REGION} cp ./packaged-template.yml s3://${S3_BUCKET}/${PROJECT_NAME}/template.yml
aws cloudformation deploy --profile=${AWS_PROFILE} --region=${AWS_REGION} --template-file packaged-template.yml --stack-name ${PROJECT_NAME} --capabilities CAPABILITY_IAM
