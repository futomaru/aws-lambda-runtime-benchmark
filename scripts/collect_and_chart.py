#!/usr/bin/env python3
"""Collect X-Ray metrics and generate benchmark chart."""

import json
from datetime import datetime, timedelta, timezone

import boto3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STACK_NAME = "aws-lambda-runtime-benchmark"

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


def get_xray_metrics(function_names):
    """X-Ray トレースから Init Duration, Invocation Duration, Overhead を取得する。"""
    xray = boto3.client("xray")
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=10)

    results = {}
    for label, func_name in function_names.items():
        filter_expr = f'service("{func_name}")'
        summaries = []
        paginator = xray.get_paginator("get_trace_summaries")
        for page in paginator.paginate(
            StartTime=start_time,
            EndTime=end_time,
            FilterExpression=filter_expr,
        ):
            summaries.extend(page.get("TraceSummaries", []))

        if not summaries:
            print(f"  WARN: {label} ({func_name}) のトレースが見つかりません")
            continue

        # 最新のトレースを1件取得
        summaries.sort(key=lambda s: s.get("ResponseTime", 0), reverse=True)
        trace_ids = [s["Id"] for s in summaries[:1]]

        traces_resp = xray.batch_get_traces(TraceIds=trace_ids)

        for trace in traces_resp.get("Traces", []):
            for segment in trace.get("Segments", []):
                doc = json.loads(segment["Document"])

                # AWS::Lambda セグメント（Lambda サービス側）に Init/Invocation がある
                if doc.get("origin") != "AWS::Lambda":
                    continue

                init_duration = 0.0
                invocation_duration = 0.0
                overhead_duration = 0.0

                for subseg in doc.get("subsegments", []):
                    duration = (subseg["end_time"] - subseg["start_time"]) * 1000
                    if subseg.get("name") == "Initialization":
                        init_duration = duration
                    elif subseg.get("name") == "Invocation":
                        invocation_duration = duration
                    elif subseg.get("name") == "Overhead":
                        overhead_duration = duration

                results[label] = {
                    "init_duration_ms": round(init_duration, 1),
                    "invocation_duration_ms": round(invocation_duration, 1),
                    "overhead_duration_ms": round(overhead_duration, 1),
                }
                break

    return results


def generate_chart(results):
    """横棒積み上げグラフを生成して benchmark_results.png に保存する。"""
    # 合計時間の昇順（速い順が上）でソート
    sorted_runtimes = sorted(
        results.keys(),
        key=lambda r: (
            results[r]["init_duration_ms"]
            + results[r]["invocation_duration_ms"]
            + results[r]["overhead_duration_ms"]
        ),
    )

    labels = sorted_runtimes
    init_durations = [results[r]["init_duration_ms"] for r in sorted_runtimes]
    invocation_durations = [results[r]["invocation_duration_ms"] for r in sorted_runtimes]
    overhead_durations = [results[r]["overhead_duration_ms"] for r in sorted_runtimes]

    fig, ax = plt.subplots(figsize=(10, 6))

    # 3色積み上げ: Init → Invocation → Overhead
    bars_init = ax.barh(
        labels, init_durations,
        label="Init Duration (Cold Start)", color="#e74c3c",
    )
    left_after_init = init_durations
    bars_invoc = ax.barh(
        labels, invocation_durations,
        left=left_after_init,
        label="Invocation Duration", color="#3498db",
    )
    left_after_invoc = [a + b for a, b in zip(init_durations, invocation_durations)]
    bars_overhead = ax.barh(
        labels, overhead_durations,
        left=left_after_invoc,
        label="Overhead", color="#95a5a6",
    )

    # バー内に ms 値を表示（幅が狭すぎる場合はスキップ）
    for bar, val in zip(bars_init, init_durations):
        if val > 20:
            ax.text(
                bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}ms", ha="center", va="center",
                fontsize=9, color="white", fontweight="bold",
            )

    for bar, val, left in zip(bars_invoc, invocation_durations, left_after_init):
        if val > 20:
            ax.text(
                left + val / 2, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}ms", ha="center", va="center",
                fontsize=9, color="white", fontweight="bold",
            )

    for bar, val, left in zip(bars_overhead, overhead_durations, left_after_invoc):
        if val > 20:
            ax.text(
                left + val / 2, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}ms", ha="center", va="center",
                fontsize=9, color="white", fontweight="bold",
            )

    # バー右端に合計値を表示
    for i, r in enumerate(sorted_runtimes):
        total = (
            results[r]["init_duration_ms"]
            + results[r]["invocation_duration_ms"]
            + results[r]["overhead_duration_ms"]
        )
        ax.text(
            total + 5, i, f"{total:.0f}ms",
            ha="left", va="center", fontsize=9, fontweight="bold",
        )

    today = datetime.now().strftime("%Y-%m-%d")
    ax.set_title(f"AWS Lambda Cold Start Benchmark ({today})", fontsize=14, fontweight="bold")
    ax.set_xlabel("Time (ms)")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    plt.savefig("benchmark_results.png", dpi=150)
    plt.close()
    print("Chart saved: benchmark_results.png")


def main():
    print("Lambda 関数名を取得中...")
    function_names = get_function_names()
    for label, name in function_names.items():
        print(f"  {label}: {name}")

    print("X-Ray メトリクスを収集中...")
    results = get_xray_metrics(function_names)

    if not results:
        print("ERROR: どのランタイムのトレースも取得できませんでした。")
        raise SystemExit(1)

    # JSON に保存
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    with open("benchmark_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved: benchmark_results.json ({len(results)}/{len(RUNTIMES)} runtimes)")

    # グラフ生成
    print("グラフを生成中...")
    generate_chart(results)


if __name__ == "__main__":
    main()
