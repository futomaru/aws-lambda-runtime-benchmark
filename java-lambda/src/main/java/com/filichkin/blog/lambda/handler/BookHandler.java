package com.filichkin.blog.lambda.handler;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.filichkin.blog.lambda.model.Book;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.PutItemRequest;

import java.util.Map;
import java.util.UUID;

// 標準 JVM（GraalVM Native Image 非使用）でのコールドスタートを計測する。
// JIT ウォームアップの影響を受けるため、JVM 系言語は初回実行が相対的に遅い点に注意。
public class BookHandler implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {

    // コールドスタートの初期化コストを計測するため、クライアント・ObjectMapper・
    // テーブル名はハンドラ外（static）で一度だけ初期化する。
    private static final DynamoDbClient DYNAMO_DB = DynamoDbClient.create();
    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final String TABLE_NAME = System.getenv("TABLE_NAME");

    @Override
    public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent event, Context context) {
        Book book;
        try {
            JsonNode node = MAPPER.readTree(event.getBody());
            book = new Book(
                    UUID.randomUUID().toString(),
                    node.get("name").asText(),
                    node.get("author").asText());
        } catch (Exception e) {
            return new APIGatewayProxyResponseEvent().withStatusCode(400);
        }

        DYNAMO_DB.putItem(PutItemRequest.builder()
                .tableName(TABLE_NAME)
                .item(Map.of(
                        "id", AttributeValue.builder().s(book.id()).build(),
                        "name", AttributeValue.builder().s(book.name()).build(),
                        "author", AttributeValue.builder().s(book.author()).build()
                ))
                .build());

        try {
            return new APIGatewayProxyResponseEvent()
                    .withStatusCode(201)
                    .withHeaders(Map.of("Content-Type", "application/json"))
                    .withBody(MAPPER.writeValueAsString(book));
        } catch (Exception e) {
            return new APIGatewayProxyResponseEvent().withStatusCode(500);
        }
    }
}
