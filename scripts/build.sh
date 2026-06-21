#!/bin/sh
set -e

# デプロイ用 S3 バケットを明示的に用意する。
# `--resolve-s3` はマネージドバケットを作成した直後にアップロードするため、
# S3 のバケット作成伝播が間に合わず "S3 Bucket does not exist" になる競合がある。
# アカウント固有の固定バケットを冪等に作成しておくことでこれを回避する。
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-ap-northeast-1}}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="aws-lambda-runtime-benchmark-${ACCOUNT_ID}"

if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "Creating deployment bucket: s3://$BUCKET ($REGION)"
  aws s3 mb "s3://$BUCKET" --region "$REGION"
fi

sam build

sam deploy --no-confirm-changeset --no-fail-on-empty-changeset \
  --stack-name aws-lambda-runtime-benchmark \
  --s3-bucket "$BUCKET" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM
