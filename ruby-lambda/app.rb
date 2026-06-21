require 'json'
require 'securerandom'
require 'aws-sdk-dynamodb'

# コールドスタートの初期化コストを計測するため、クライアントとテーブル名は
# ハンドラ外（グローバルスコープ）で一度だけ初期化する。
CLIENT = Aws::DynamoDB::Client.new
TABLE_NAME = ENV.fetch('TABLE_NAME')

def create(event:, context:)
  data = JSON.parse(event['body'])

  book = {
    'id' => SecureRandom.uuid,
    'name' => data['name'],
    'author' => data['author']
  }

  CLIENT.put_item(table_name: TABLE_NAME, item: book)

  {
    statusCode: 201,
    headers: { 'Content-Type' => 'application/json' },
    body: JSON.generate(book)
  }
end
