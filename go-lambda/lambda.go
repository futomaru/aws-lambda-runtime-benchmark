package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/google/uuid"
)

var client *dynamodb.Client

type Book struct {
	Id     string `json:"id" dynamodbav:"id"`
	Author string `json:"author" dynamodbav:"author"`
	Name   string `json:"name" dynamodbav:"name"`
}

func Handler(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	var input Book
	json.Unmarshal([]byte(request.Body), &input)

	book := Book{
		Id:     uuid.New().String(),
		Author: input.Author,
		Name:   input.Name,
	}

	av, err := attributevalue.MarshalMap(book)
	if err != nil {
		fmt.Println("Error marshalling item:", err.Error())
		return events.APIGatewayProxyResponse{StatusCode: 500}, nil
	}

	_, err = client.PutItem(ctx, &dynamodb.PutItemInput{
		Item:      av,
		TableName: strPtr("book"),
	})
	if err != nil {
		fmt.Println("Error calling PutItem:", err.Error())
		return events.APIGatewayProxyResponse{StatusCode: 500}, nil
	}

	body, _ := json.Marshal(book)
	return events.APIGatewayProxyResponse{Body: string(body), StatusCode: 201}, nil
}

func strPtr(s string) *string { return &s }

func main() {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		panic("unable to load SDK config: " + err.Error())
	}
	client = dynamodb.NewFromConfig(cfg)
	lambda.Start(Handler)
}
