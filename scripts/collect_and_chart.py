#!/usr/bin/env python3
"""Collect CloudWatch Logs metrics and generate benchmark chart."""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STACK_NAME = "aws-lambda-runtime-benchmark"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# template.yaml の論理ID → グラフ表示ラベル
RUNTIMES = {
    "PythonFunction": "Python",
    "NodeJsFunction": "Node.js",
    "RubyFunction": "Ruby",
    "JavaFunction": "Java",
    "DotNetFunction": ".NET",
    "GoFunction": "Go",
    "RustFunction": "Rust",
}


def get_function_names():
    """CloudFormation スタックから実際の Lambda 関数名を取得する。"""
    cfn = boto3.client("cloudformation")
    function_names = {}
    for logical_id, label in RUNTIMES.items():
        resp = cfn.describe_stack_resource(
            StackName=STACK_NAME,
            LogicalResourceId=logical_id,
        )
        physical_id = resp["StackResourceDetail"]["PhysicalResourceId"]
        function_names[label] = physical_id
    return function_names


def get_cloudwatch_metrics(function_names):
    """CloudWatch Logs の REPORT 行から Init Duration と Duration を取得する。"""
    logs = boto3.client("logs")
    end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = end_time - 10 * 60 * 1000  # 過去10分間

    report_re = re.compile(
        r"Duration:\s+(?P<duration>[\d.]+)\s+ms.*"
        r"Init Duration:\s+(?P<init>[\d.]+)\s+ms"
    )

    results = {}
    for label, func_name in function_names.items():
        log_group = f"/aws/lambda/{func_name}"
        try:
            resp = logs.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                endTime=end_time,
                filterPattern="REPORT Init Duration",
                limit=1,
            )
        except logs.exceptions.ResourceNotFoundException:
            print(f"  WARN: {label} ロググループが見つかりません: {log_group}")
            continue

        events = resp.get("events", [])
        if not events:
            print(f"  WARN: {label} ({func_name}) の REPORT 行が見つかりません")
            continue

        # 最新のイベントを使用
        message = events[-1]["message"]
        m = report_re.search(message)
        if not m:
            print(f"  WARN: {label} REPORT 行のパースに失敗: {message}")
            continue

        results[label] = {
            "init_duration_ms": round(float(m.group("init")), 1),
            "invocation_duration_ms": round(float(m.group("duration")), 1),
        }
        print(f"  {label}: Init={m.group('init')}ms, Duration={m.group('duration')}ms")

    return results


def generate_chart(results):
    """横棒積み上げグラフを生成して benchmark_results.png に保存する。"""
    # 合計時間の昇順（速い順が上）でソート
    sorted_runtimes = sorted(
        results.keys(),
        key=lambda r: (
            results[r]["init_duration_ms"]
            + results[r]["invocation_duration_ms"]
        ),
    )

    init_durations = [results[r]["init_duration_ms"] for r in sorted_runtimes]
    invocation_durations = [results[r]["invocation_duration_ms"] for r in sorted_runtimes]
    totals = [i + v for i, v in zip(init_durations, invocation_durations)]
    max_total = max(totals)

    fig, ax = plt.subplots(figsize=(12, 6))

    # 2色積み上げ: Init → Invocation
    bars_init = ax.barh(
        sorted_runtimes, init_durations,
        label="Init Duration (Cold Start)", color="#e74c3c",
    )
    bars_invoc = ax.barh(
        sorted_runtimes, invocation_durations,
        left=init_durations,
        label="Invocation Duration", color="#3498db",
    )

    # バー内テキスト: 全体の10%以上の幅があるバーのみ表示
    min_bar_width = max_total * 0.10

    for bar, val in zip(bars_init, init_durations):
        if val >= min_bar_width:
            ax.text(
                bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}ms", ha="center", va="center",
                fontsize=9, color="white", fontweight="bold",
            )

    for bar, val, left in zip(bars_invoc, invocation_durations, init_durations):
        if val >= min_bar_width:
            ax.text(
                left + val / 2, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}ms", ha="center", va="center",
                fontsize=9, color="white", fontweight="bold",
            )

    # バー右端にラベル表示: 内訳が見えないバーがあれば "(init + invocation)" 形式で補足
    for i, (r, init, invoc, total) in enumerate(
        zip(sorted_runtimes, init_durations, invocation_durations, totals)
    ):
        if init < min_bar_width or invoc < min_bar_width:
            label = f"{total:.0f}ms ({init:.0f} + {invoc:.0f})"
        else:
            label = f"{total:.0f}ms"
        ax.text(
            total + max_total * 0.015, i, label,
            ha="left", va="center", fontsize=9, fontweight="bold",
        )

    # 右端のラベルが切れないよう余白を確保
    ax.set_xlim(right=max_total * 1.25)

    today = datetime.now().strftime("%Y-%m-%d")
    ax.set_title(f"AWS Lambda Cold Start Benchmark ({today})", fontsize=14, fontweight="bold")
    ax.set_xlabel("Time (ms)")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    chart_path = PROJECT_ROOT / "images" / "benchmark_results.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()
    print(f"Chart saved: {chart_path}")


def main():
    print("Lambda 関数名を取得中...")
    function_names = get_function_names()
    for label, name in function_names.items():
        print(f"  {label}: {name}")

    print("CloudWatch Logs からメトリクスを収集中...")
    results = get_cloudwatch_metrics(function_names)

    if not results:
        print("ERROR: どのランタイムのトレースも取得できませんでした。")
        raise SystemExit(1)

    # JSON に保存
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    json_path = PROJECT_ROOT / "scripts" / "benchmark_results.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved: {json_path} ({len(results)}/{len(RUNTIMES)} runtimes)")

    # グラフ生成
    print("グラフを生成中...")
    generate_chart(results)


if __name__ == "__main__":
    main()
