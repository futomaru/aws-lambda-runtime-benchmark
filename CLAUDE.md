# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AWS Lambda コールドスタートベンチマーク。7つのランタイム（Python, Node.js, Ruby, Java, .NET, Go, Rust）がすべて同一のワークロード（DynamoDB への書き込み）を実行し、レスポンスタイムを比較する。

アーキテクチャ: `Client → API Gateway → Lambda (各ランタイム) → DynamoDB`

すべての Lambda 関数は ARM64 / 256 MB で動作。Go と Rust のみ `provided.al2023` ランタイムを使い、各 Makefile でクロスコンパイルする。

## ベンチマーク実行フロー

ベンチマークは以下の順序で実施する（前提：AWS CLI と SAM CLI が設定済みであること）:

```bash
# 1. ビルドとデプロイ（sam build + sam deploy）
./scripts/build.sh

# 2. コールドスタットを強制したうえで全ランタイムへリクエスト送信
./scripts/test.sh

# 3. CloudWatch Logs から直近10分のメトリクスを収集してグラフ生成
pip install -r scripts/requirements.txt
python scripts/collect_and_chart.py
```

`test.sh` は Lambda の環境変数を更新してコールドスタートを強制してから curl を実行する。`collect_and_chart.py` は `test.sh` 実行から **15秒以上待ってから**実行すること（ログが CloudWatch に届くまでのラグ）。

CI/CD（`.github/workflows/deploy.yaml`）はこの一連の流れを自動化し、生成されたグラフと JSON を main ブランチにコミットして返す。

## SAM スタック構成

- スタック名: `aws-lambda-runtime-benchmark`
- AWS リージョン: `ap-northeast-1`
- Go / Rust は `BuildMethod: makefile` を使用（`sam build` が各 Makefile の `build-<LogicalID>` ターゲットを呼び出す）

## 成果物

| ファイル | 役割 |
|---|---|
| `images/benchmark_results.png` | コールドスタート（Init Duration + Invocation Duration）の積み上げ横棒グラフ |
| `images/benchmark_memory.png` | Max Memory Used の横棒グラフ |
| `scripts/benchmark_results.json` | 最新のメトリクス JSON |

これらは CI が自動更新する。手動更新する場合は `collect_and_chart.py` を直接実行する。

## 各ランタイムの追加情報

- **Go**: `GOOS=linux GOARCH=arm64 CGO_ENABLED=0` でクロスコンパイル、`bootstrap` バイナリを生成
- **Rust**: `cargo lambda build --release --arm64` を使用（`cargo-lambda` が必要。edition 2024 / toolchain 1.96.0）。インストールは `pip install cargo-lambda` が引き続き有効（公式推奨の筆頭は Homebrew / curl。なお `cargo install cargo-lambda` は crates.io 非公開のため不可）
- **Java**: Maven プロジェクト（`java-lambda/pom.xml`）、JDK 25 が必要。JSON は jackson-databind を使用
- **Ruby**: `ruby4.0`。`ruby-lambda/Gemfile` に `aws-sdk-dynamodb` を明示
- **環境変数**: テーブル名は全ランタイムで `TABLE_NAME`（`template.yaml` の Globals から `!Ref BooksTable` で注入）。`test.sh` でコールドスタートを強制する際も `TABLE_NAME=book` を保持すること
