package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/google/uuid"
)

// コールドスタートの初期化コストを計測するため、クライアントとテーブル名は
// main()（ハンドラ外）で一度だけ初期化する。
var (
	client    *dynamodb.Client
	tableName string
)

type Book struct {
	Id     string `json:"id" dynamodbav:"id"`
	Name   string `json:"name" dynamodbav:"name"`
	Author string `json:"author" dynamodbav:"author"`
}

func Handler(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	var input Book
	if err := json.Unmarshal([]byte(request.Body), &input); err != nil {
		fmt.Println("Error unmarshalling request body:", err.Error())
		return events.APIGatewayProxyResponse{StatusCode: 400}, nil
	}

	book := Book{
		Id:     uuid.New().String(),
		Name:   input.Name,
		Author: input.Author,
	}

	av, err := attributevalue.MarshalMap(book)
	if err != nil {
		fmt.Println("Error marshalling item:", err.Error())
		return events.APIGatewayProxyResponse{StatusCode: 500}, nil
	}

	_, err = client.PutItem(ctx, &dynamodb.PutItemInput{
		Item:      av,
		TableName: aws.String(tableName),
	})
	if err != nil {
		fmt.Println("Error calling PutItem:", err.Error())
		return events.APIGatewayProxyResponse{StatusCode: 500}, nil
	}

	body, _ := json.Marshal(book)
	return events.APIGatewayProxyResponse{
		StatusCode: 201,
		Headers:    map[string]string{"Content-Type": "application/json"},
		Body:       string(body),
	}, nil
}

func main() {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		panic("unable to load SDK config: " + err.Error())
	}
	client = dynamodb.NewFromConfig(cfg)
	tableName = os.Getenv("TABLE_NAME")
	lambda.Start(Handler)
}
