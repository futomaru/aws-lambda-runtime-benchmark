#!/bin/sh
set -e

sam build

sam deploy --no-confirm-changeset --no-fail-on-empty-changeset \
  --stack-name aws-lambda-runtime-benchmark \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM
