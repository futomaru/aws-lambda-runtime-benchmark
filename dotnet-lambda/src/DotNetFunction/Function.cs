using System.Text.Json;
using System.Text.Json.Serialization;
using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.Core;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace DotNetFunction;

// 標準 JVM 相当の通常実行（AOT 非使用）でのコールドスタートを計測する。
// JIT ウォームアップの影響を受ける点に注意。
public class Function
{
    // コールドスタートの初期化コストを計測するため、クライアントとテーブル名は
    // ハンドラ外（static）で一度だけ初期化する。
    private static readonly AmazonDynamoDBClient _dbClient = new();
    private static readonly string TableName = Environment.GetEnvironmentVariable("TABLE_NAME")!;

    public async Task<APIGatewayProxyResponse> FunctionHandler(APIGatewayProxyRequest apigProxyEvent, ILambdaContext context)
    {
        // Source Generator 由来の JsonTypeInfo を使い、リフレクションを避けて (de)serialize する。
        var book = JsonSerializer.Deserialize(apigProxyEvent.Body, BookJsonContext.Default.Book)!;
        book.id = Guid.NewGuid().ToString();

        var request = new PutItemRequest
        {
            TableName = TableName,
            Item = new Dictionary<string, AttributeValue>
            {
                { "id", new AttributeValue { S = book.id } },
                { "name", new AttributeValue { S = book.name } },
                { "author", new AttributeValue { S = book.author } }
            }
        };
        await _dbClient.PutItemAsync(request);

        return new APIGatewayProxyResponse
        {
            Body = JsonSerializer.Serialize(book, BookJsonContext.Default.Book),
            StatusCode = 201,
            Headers = new Dictionary<string, string> { { "Content-Type", "application/json" } }
        };
    }
}

// System.Text.Json Source Generator: Book のシリアライザをコンパイル時に生成する。
[JsonSerializable(typeof(Book))]
public partial class BookJsonContext : JsonSerializerContext
{
}
