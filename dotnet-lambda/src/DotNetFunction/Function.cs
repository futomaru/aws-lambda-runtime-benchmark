using System.Text.Json;
using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.Core;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace DotNetFunction;

public class Function
{
    private static readonly AmazonDynamoDBClient _dbClient = new();

    public async Task<APIGatewayProxyResponse> FunctionHandler(APIGatewayProxyRequest apigProxyEvent, ILambdaContext context)
    {
        var book = JsonSerializer.Deserialize<Book>(apigProxyEvent.Body)!;
        book.id = Guid.NewGuid().ToString();

        var request = new PutItemRequest
        {
            TableName = "book",
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
            Body = JsonSerializer.Serialize(book),
            StatusCode = 201,
            Headers = new Dictionary<string, string> { { "Content-Type", "application/json" } }
        };
    }
}
