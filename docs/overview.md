# aws-lambda-runtime-benchmark リポジトリ概要

## 目的

**AWS Lambda の各ランタイム（プログラミング言語）のパフォーマンス（特にコールドスタート時間）を比較するベンチマークプロジェクト。**

全ランタイムで同じ処理（DynamoDB への書き込み）を実装し、条件を揃えて速度を計測する。

## 対象ランタイム

| 言語 | ランタイム | SAM Runtime |
|------|-----------|-------------|
| Python | 3.14 | python3.14 |
| Node.js | 24.x | nodejs24.x |
| Ruby | 3.4 | ruby3.4 |
| Java | 25 | java25 |
| .NET | 10 | dotnet10 |
| Go | 1.23 | provided.al2023 |
| Rust | latest | provided.al2023 |

全て **ARM64 (Graviton)**, メモリ **256MB** で統一。合計 **7 個の Lambda 関数**をデプロイして比較する。

## アーキテクチャ

```
クライアント → API Gateway → Lambda (各ランタイム) → DynamoDB
```

全関数が共通で「本 (book) の情報を受け取り、UUID を付与して DynamoDB に保存する」という処理を行う。

## ディレクトリ構成

```
├── python-lambda/          # Python 実装
├── node-lambda/            # Node.js 実装
├── ruby-lambda/            # Ruby 実装
├── java-lambda/            # Java 実装
├── dotnet-lambda/          # .NET 実装
├── go-lambda/              # Go 実装
├── rust-lambda/            # Rust 実装
├── template.yaml           # SAM テンプレート（全ランタイム定義）
├── build.sh                # sam build + sam deploy
├── test.sh                 # curl による簡易パフォーマンステスト
└── .github/workflows/      # GitHub Actions CI/CD
```

## ビルド・デプロイ

- **AWS SAM** でインフラ定義・デプロイ
- **GitHub Actions** (`deploy.yaml`) で CI/CD を自動化
- `build.sh` で `sam build` → `sam deploy` を一括実行

## パフォーマンステスト

- `test.sh` — curl で各エンドポイント (7種) にリクエストし、応答時間を計測
