#!/bin/bash
# install dependendies into target folder and create lambda zip package

# build folder
TARGET_FOLDER=./target
ZIP_FILE=./lambda.zip

# target folder does not exist, install dependencies
if [ ! -d "$TARGET_FOLDER" ]; then
  pip install -r requirements.txt --target $TARGET_FOLDER
fi

cp ./src/* $TARGET_FOLDER
chmod -R 755 $TARGET_FOLDER
rm -f $ZIP_FILE
cd $TARGET_FOLDER
zip -r ../$ZIP_FILE .
cd ..

# upload zip package + template
#aws cloudformation package --template-file ./template.yml --s3-bucket $S3_BUCKET --s3-prefix $S3_PREFIX --output-template-file packaged-template.yml
#aws s3 cp ./packaged-template.yml s3://$S3_BUCKET/$S3_PREFIX/template.yml