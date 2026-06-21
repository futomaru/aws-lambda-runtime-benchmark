"""Python Lambda benchmark function (boto3 resource API)."""

import json
import os
import uuid
from typing import Any

import boto3

# コールドスタートの初期化コストを計測するため、クライアントとテーブル名は
# ハンドラ外（モジュールスコープ）で一度だけ初期化する。
dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)


def create(event: dict[str, Any], context: Any) -> dict[str, Any]:
    data = json.loads(event["body"])

    item = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "author": data["author"],
    }

    table.put_item(Item=item)

    return {
        "statusCode": 201,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(item),
    }
