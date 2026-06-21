# AWS Lambda Runtime Benchmark

AWS Lambda の各ランタイムのパフォーマンス（特にコールドスタート）を比較するベンチマークプロジェクト。

全ランタイムで同一処理（DynamoDB への書き込み）を ARM64 / 256MB の統一条件で実行し、応答時間を計測する。

## アーキテクチャ

![Architecture](images/arch-diagram.svg)

```
クライアント → API Gateway → Lambda (各ランタイム) → DynamoDB
```

## 対象ランタイム

| 言語 | バージョン | SAM Runtime |
|------|-----------|-------------|
| Python | 3.14 | python3.14 |
| Node.js | 24.x | nodejs24.x |
| Ruby | 4.0 | ruby4.0 |
| Java | 25 | java25 |
| .NET | 10 | dotnet10 |
| Go | 1.26 | provided.al2023 |
| Rust | 1.96.0 | provided.al2023 |

## 対照実験としての設計

実装は言語ごとに異なるが、**実験条件**を完全に揃えることで、計測差が「テスト設定」では
なく「ランタイムそのもの」を反映するように設計している。

- **全関数で同一条件**: ARM64 (Graviton) / 256 MB / タイムアウト 15 秒 / X-Ray Active
  トレース、ワークロードも同一（DynamoDB への `PutItem` 1 回）。
- **コールドスタート初期化を公平に計測**: DynamoDB クライアントを全ランタイムで
  ハンドラ外（モジュール／グローバルスコープ）に初期化し、接続・SDK 初期化コストが
  `Init Duration` に乗るようにしている。
- **設定のハードコードを排除**: テーブル名は単一ソース（`!Ref BooksTable`）から
  `TABLE_NAME` 環境変数で全関数に統一注入する。
- **統一された入出力契約**: 全関数が `{name, author}` を受け取り、UUID で `id` を生成し、
  `201` の JSON レスポンスを返す。
- **JIT に関する注記**: Java / .NET は標準 JVM/CLR で動作（GraalVM/AOT 非使用）するため、
  コールドスタート時に JIT ウォームアップのコストが乗る。これは比較対象として意図的に
  含めている。

## ベンチマーク結果

![Benchmark Results](images/benchmark_results.png)
![Memory Usage](images/benchmark_memory.png)

*CI/CD パイプラインで自動更新*

## ビルド・デプロイ

前提: AWS SAM CLI、AWS アカウント、S3 バケット `aws-lambda-runtime-benchmark`

```bash
./scripts/build.sh    # sam build → sam deploy を一括実行
```

GitHub Actions (`.github/workflows/deploy.yaml`) による CI/CD も利用可能。

## テスト

```bash
./scripts/test.sh     # 全ランタイムに curl でリクエストし応答時間を計測
```
