use aws_sdk_dynamodb::types::AttributeValue;
use aws_sdk_dynamodb::Client;
use lambda_http::{run, service_fn, Body, Error, Request, Response};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Serialize, Deserialize)]
struct Book {
    id: Option<String>,
    name: String,
    author: String,
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .without_time()
        .with_max_level(tracing::Level::INFO)
        .init();

    // コールドスタートの初期化コストを計測するため、クライアントとテーブル名は
    // main()（ハンドラ外）で一度だけ初期化する。
    let config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
    let client = Client::new(&config);
    let table_name = std::env::var("TABLE_NAME")?;

    run(service_fn(|event: Request| {
        let client = client.clone();
        let table_name = table_name.clone();
        async move { handle_request(event, &client, &table_name).await }
    }))
    .await
}

async fn handle_request(event: Request, client: &Client, table_name: &str) -> Result<Response<Body>, Error> {
    let body = match event.body() {
        Body::Text(text) => text.clone(),
        _ => {
            return Ok(Response::builder()
                .status(400)
                .body("Empty body".into())?);
        }
    };

    let mut book: Book = serde_json::from_str(&body)?;
    let id = Uuid::new_v4().to_string();
    book.id = Some(id.clone());

    client
        .put_item()
        .table_name(table_name)
        .item("id", AttributeValue::S(id))
        .item("name", AttributeValue::S(book.name.clone()))
        .item("author", AttributeValue::S(book.author.clone()))
        .send()
        .await?;

    let json = serde_json::to_string(&book)?;
    Ok(Response::builder()
        .status(201)
        .header("content-type", "application/json")
        .body(json.into())?)
}
