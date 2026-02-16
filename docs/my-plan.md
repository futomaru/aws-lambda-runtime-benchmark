## 目的
AWS Lambda の各ランタイム（プログラミング言語）のパフォーマンスを比較するベンチマークプロジェクト。

全ランタイムで同じ処理（DynamoDB への書き込み）を実装し、条件を揃えて速度を計測する。

## 最新のサポートランタイムが対象
- .NET 10 (C#)
- Java 25
- Node.js 24.x
- Python 3.14
- Ruby 3.4
- Amazon Linux 2023
    - Go
    - Rust

すべて arm とする

## アーキテクチャ

```
クライアント → API Gateway → Lambda (各ランタイム) → DynamoDB
```

全関数が共通で「本 (book) の情報を受け取り、UUID を付与して DynamoDB に保存する」という処理を行う。メモリは全関数 256MB で統一。

## ビルド・デプロイ

- **AWS SAM** でインフラ定義・デプロイ
- **GitHub Actions** (`deploy.yaml`) で CI/CD を自動化
- `build.sh` で全ランタイムを一括ビルドし `sam deploy` でデプロイ

## パフォーマンステスト

- **簡易テスト**: `test.sh` — curl で各エンドポイントにリクエストし、応答時間を計測

## 方針
- 実装は最小構成 MVP であること。
