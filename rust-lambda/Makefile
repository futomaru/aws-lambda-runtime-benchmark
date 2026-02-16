build-RustFunction:
	cargo lambda build --release --arm64 --output-format zip
	cp target/lambda/rust-lambda/bootstrap $(ARTIFACTS_DIR)/bootstrap
