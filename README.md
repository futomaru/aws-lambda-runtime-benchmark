# AWS Lambda Runtime Benchmark

AWS Lambda の各ランタイムのパフォーマンス（特にコールドスタート）を比較するベンチマークプロジェクト。

全ランタイムで同一処理（DynamoDB への書き込み）を ARM64 / 256MB の統一条件で実行し、応答時間を計測する。

## アーキテクチャ

```
クライアント → API Gateway → Lambda (各ランタイム) → DynamoDB
```

## 対象ランタイム

| 言語 | バージョン | SAM Runtime |
|------|-----------|-------------|
| Python | 3.14 | python3.14 |
| Node.js | 24.x | nodejs24.x |
| Ruby | 3.4 | ruby3.4 |
| Java | 25 | java25 |
| .NET | 10 | dotnet10 |
| Go | 1.23 | provided.al2023 |
| Rust | latest | provided.al2023 |

## ビルド・デプロイ

前提: AWS SAM CLI、AWS アカウント、S3 バケット `aws-lambda-runtime-benchmark`

```bash
./build.sh    # sam build → sam deploy を一括実行
```

GitHub Actions (`.github/workflows/deploy.yaml`) による CI/CD も利用可能。

## テスト

```bash
./test.sh     # 全ランタイムに curl でリクエストし応答時間を計測
```
