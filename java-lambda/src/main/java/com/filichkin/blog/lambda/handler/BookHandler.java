package com.filichkin.blog.lambda.handler;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import com.filichkin.blog.lambda.model.Book;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.PutItemRequest;

import java.util.Map;
import java.util.UUID;

public class BookHandler implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {

    private static final DynamoDbClient dynamoDb = DynamoDbClient.create();
    private static final String TABLE_NAME = "book";

    @Override
    public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent event, Context context) {
        String body = event.getBody();
        String name = extractField(body, "name");
        String author = extractField(body, "author");
        String id = UUID.randomUUID().toString();

        var book = new Book(id, name, author);

        dynamoDb.putItem(PutItemRequest.builder()
                .tableName(TABLE_NAME)
                .item(Map.of(
                        "id", AttributeValue.builder().s(book.id()).build(),
                        "name", AttributeValue.builder().s(book.name()).build(),
                        "author", AttributeValue.builder().s(book.author()).build()
                ))
                .build());

        String json = """
                {"id":"%s","name":"%s","author":"%s"}""".formatted(book.id(), book.name(), book.author());

        return new APIGatewayProxyResponseEvent()
                .withStatusCode(201)
                .withBody(json);
    }

    private String extractField(String json, String field) {
        String key = "\"" + field + "\"";
        int idx = json.indexOf(key);
        int start = json.indexOf("\"", idx + key.length() + 1) + 1;
        int end = json.indexOf("\"", start);
        return json.substring(start, end);
    }
}
