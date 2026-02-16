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

    let config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
    let client = Client::new(&config);

    run(service_fn(|event: Request| {
        let client = client.clone();
        async move { handle_request(event, &client).await }
    }))
    .await
}

async fn handle_request(event: Request, client: &Client) -> Result<Response<Body>, Error> {
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
        .table_name("book")
        .item("id", AttributeValue::S(id))
        .item("name", AttributeValue::S(book.name.clone()))
        .item("author", AttributeValue::S(book.author.clone()))
        .send()
        .await?;

    let json = serde_json::to_string(&book)?;
    Ok(Response::builder().status(201).body(json.into())?)
}
