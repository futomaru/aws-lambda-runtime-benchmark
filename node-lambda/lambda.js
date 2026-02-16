import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand } from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'node:crypto';

const client = new DynamoDBClient();
const docClient = DynamoDBDocumentClient.from(client);

export const create = async (event) => {
  const data = JSON.parse(event.body);

  const item = {
    id: randomUUID(),
    name: data.name,
    author: data.author,
  };

  await docClient.send(new PutCommand({
    TableName: 'book',
    Item: item,
  }));

  return {
    statusCode: 201,
    body: JSON.stringify(item),
  };
};
