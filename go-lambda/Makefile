build-GoFunction:
	GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -tags lambda.norpc -o $(ARTIFACTS_DIR)/bootstrap lambda.go
