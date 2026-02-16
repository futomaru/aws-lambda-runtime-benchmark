#!/bin/sh
set -e

sam build

sam deploy --no-confirm-changeset --no-fail-on-empty-changeset \
  --stack-name aws-lambda-runtime-benchmark \
  --s3-bucket aws-lambda-runtime-benchmark \
  --capabilities CAPABILITY_IAM
