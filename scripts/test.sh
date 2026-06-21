#!/usr/bin/env bash
# bash 専用（プロセス置換 / read を使用）。
set -euo pipefail

STACK_NAME="aws-lambda-runtime-benchmark"
LOGICAL_IDS="PythonFunction NodeJsFunction RubyFunction JavaFunction DotNetFunction GoFunction RustFunction"

# get API endpoint (--output text で引用符なしの生値を取得)
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[0].OutputValue' --output text)

# Force cold start: update environment variable to reset execution environments
echo "===== Forcing cold start for all functions ====="
BENCHMARK_TS=$(date +%s)
for logical_id in $LOGICAL_IDS
do
  func_name=$(aws cloudformation describe-stack-resource \
    --stack-name "$STACK_NAME" \
    --logical-resource-id "$logical_id" \
    --query 'StackResourceDetail.PhysicalResourceId' \
    --output text)
  echo "Updating $logical_id ($func_name)..."
  # --environment は環境変数マップを丸ごと置換するため、TABLE_NAME=book を必ず保持する。
  # （省略すると TABLE_NAME が消え、全関数が実行時に失敗する）
  aws lambda update-function-configuration \
    --function-name "$func_name" \
    --environment "Variables={TABLE_NAME=book,BENCHMARK_TS=$BENCHMARK_TS}" \
    --no-cli-pager > /dev/null
done

# Wait for all function updates to complete
echo "Waiting for function updates to complete..."
for logical_id in $LOGICAL_IDS
do
  func_name=$(aws cloudformation describe-stack-resource \
    --stack-name "$STACK_NAME" \
    --logical-resource-id "$logical_id" \
    --query 'StackResourceDetail.PhysicalResourceId' \
    --output text)
  aws lambda wait function-updated --function-name "$func_name"
done
echo "All functions updated. Cold start will be triggered on next invocation."

# Send a request to each runtime and validate the response
RESP_BODY="$(mktemp)"
trap 'rm -f "$RESP_BODY"' EXIT
failed=0
for runtime in python node ruby java dotnet go rust
do
  echo "------------- $runtime:"
  read -r http_code time_total < <(curl -s -o "$RESP_BODY" \
    -w '%{http_code} %{time_total}' \
    -X POST --location "$API_ENDPOINT/$runtime/book" \
    -H "accept: application/json" \
    -H "content-type: application/json" \
    -d '{"name":"Sotnikov","author":"Vasil Baykoav"}')
  body="$(cat "$RESP_BODY")"
  echo "  HTTP $http_code | Total: ${time_total}s | $body"
  if [ "$http_code" != "201" ] || ! grep -q '"id"' "$RESP_BODY"; then
    echo "  ERROR: $runtime did not return a valid 201 response with an id"
    failed=1
  fi
done

if [ "$failed" -ne 0 ]; then
  echo "===== One or more runtimes failed validation ====="
  exit 1
fi
echo "===== All runtimes returned a valid 201 response ====="
