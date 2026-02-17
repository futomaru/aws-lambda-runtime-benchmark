#!/bin/sh
set -e

STACK_NAME="aws-lambda-runtime-benchmark"
LOGICAL_IDS="PythonFunction NodeJsFunction RubyFunction JavaFunction DotNetFunction GoFunction RustFunction"

# get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs[0].OutputValue')

# remove quotes
API_ENDPOINT=$(sed -e 's/^"//' -e 's/"$//' <<< "$API_ENDPOINT")

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
  aws lambda update-function-configuration \
    --function-name "$func_name" \
    --environment "Variables={BENCHMARK_TS=$BENCHMARK_TS}" \
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

for runtime in python node ruby java dotnet go rust
do
  echo "------------- $runtime:"
  curl -X POST --fail -w '\nTotal: %{time_total}s\n' --location "$API_ENDPOINT/$runtime/book" \
      -H "accept: application/json" \
      -H "content-type: application/json" \
      -d "{
            \"name\": \"Sotnikov\",
            \"author\": \"Vasil Baykoav\"
          }"
done
