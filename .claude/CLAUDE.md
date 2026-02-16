# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

AWS Lambda の7言語ランタイム（Python 3.14, Node.js 24, Ruby 3.4, Java 25, .NET 10, Go 1.23, Rust）のコールドスタートパフォーマンスを比較するベンチマーク。全関数は同一処理（API Gateway経由でbook情報を受け取り、UUIDを付与してDynamoDBに保存）をARM64/256MBの統一条件で実行する。

## アーキテクチャ

```
クライアント → API Gateway → Lambda (各ランタイム) → DynamoDB (bookテーブル)
```

- インフラ定義: `template.yaml` (AWS SAM)
- 全Lambda関数のグローバル設定（メモリ256MB、タイムアウト15秒、ARM64、X-Rayトレーシング）はtemplate.yamlのGlobalsセクションで管理
- APIエンドポイント: `/{runtime}/book` (POST)

## ビルド・デプロイ・テスト

```bash
# ビルドとデプロイ（sam build → sam deploy を一括実行）
./build.sh

# デプロイ済み全ランタイムの簡易パフォーマンステスト（curlで応答時間計測）
./test.sh
```

- CI/CD: `.github/workflows/deploy.yaml` — push/PRで全ランタイムのビルド・デプロイ・テストを自動実行
- デプロイ先リージョン: ap-northeast-1、S3バケット: `aws-lambda-runtime-benchmark`

## ランタイム別ビルド方式

| ランタイム | SAM Runtime | ビルド方式 |
|-----------|-------------|-----------|
| Python, Node.js, Ruby, Java, .NET | マネージドランタイム | SAM標準ビルド |
| Go | provided.al2023 | `go-lambda/Makefile` でクロスコンパイル（CGO_ENABLED=0, GOARCH=arm64）→ bootstrap生成 |
| Rust | provided.al2023 | `rust-lambda/Makefile` で cargo-lambda ビルド → bootstrap生成 |

Java は Maven Shade Plugin で uber-jar を生成（`java-lambda/pom.xml`）。

## 各ランタイムのエントリーポイント

- `python-lambda/lambda.py` — handler関数
- `node-lambda/lambda.js` — ES Module形式、handler関数
- `ruby-lambda/app.rb` — handler関数
- `java-lambda/src/main/java/com/filichkin/blog/lambda/handler/BookHandler.java`
- `dotnet-lambda/src/DotNetFunction/Function.cs`
- `go-lambda/lambda.go` — main関数
- `rust-lambda/src/main.rs` — main関数

## 開発方針

- 実装は最小構成MVP。余計な抽象化やフレームワークは使わない
- 全ランタイムで条件を揃える（ARM64、256MB、同一処理）
- 最新のサポートランタイムバージョンを対象とする
