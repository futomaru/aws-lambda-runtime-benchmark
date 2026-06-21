import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand } from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'node:crypto';

// コールドスタートの初期化コストを計測するため、クライアントとテーブル名は
// ハンドラ外（モジュールスコープ）で一度だけ初期化する。
const client = new DynamoDBClient();
const docClient = DynamoDBDocumentClient.from(client);
const TABLE_NAME = process.env.TABLE_NAME;

export const create = async (event) => {
  const data = JSON.parse(event.body);

  const item = {
    id: randomUUID(),
    name: data.name,
    author: data.author,
  };

  await docClient.send(new PutCommand({
    TableName: TABLE_NAME,
    Item: item,
  }));

  return {
    statusCode: 201,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  };
};
