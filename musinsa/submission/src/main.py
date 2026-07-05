from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mapper import available_keywords, build_mapping_result, find_signal, load_trend_signals
from report_generator import generate_markdown_report, write_report
from scorer import build_score_result


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SIGNALS = BASE_DIR / "data" / "sample_trend_signals.json"
DEFAULT_CATEGORIES = BASE_DIR / "data" / "sample_musinsa_categories.csv"
DEFAULT_TAGS = BASE_DIR / "data" / "sample_musinsa_tags.csv"
DEFAULT_CATALOG = BASE_DIR / "data" / "sample_musinsa_catalog.csv"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"


def build_trend_report(
    keyword: str,
    signals_path: Path = DEFAULT_SIGNALS,
    categories_path: Path = DEFAULT_CATEGORIES,
    tags_path: Path = DEFAULT_TAGS,
    catalog_path: Path = DEFAULT_CATALOG,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    payload = load_trend_signals(signals_path)
    signal = find_signal(keyword, payload)
    mapping_result = build_mapping_result(keyword, signal, categories_path, tags_path, catalog_path)
    score_result = build_score_result(signal, mapping_result["category_connection_score"])
    markdown = generate_markdown_report(
        keyword=keyword,
        signal=signal,
        score_result=score_result,
        mapping_result=mapping_result,
        source_files={
            "트렌드 신호": str(signals_path),
            "카테고리": str(categories_path),
            "태그": str(tags_path),
            "상품 카탈로그": str(catalog_path),
        },
    )
    output_path = write_report(output_dir, keyword, markdown)
    return {
        "keyword": keyword,
        "output_path": str(output_path),
        "signal": signal,
        "score_result": score_result,
        "mapping_result": mapping_result,
        "markdown": markdown,
        "available_keywords": available_keywords(payload),
    }


def parse_cli_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="무신사 트렌드 신호 검증 MVP: 키워드 점수와 Markdown 리포트를 생성합니다."
    )
    parser.add_argument("keyword_arg", nargs="?", help="평가할 트렌드 키워드입니다.")
    parser.add_argument("--keyword", dest="keyword_option", help="평가할 트렌드 키워드입니다.")
    parser.add_argument("--signals", default=str(DEFAULT_SIGNALS), help="mock 트렌드 신호 JSON 경로입니다.")
    parser.add_argument("--categories", default=str(DEFAULT_CATEGORIES), help="무신사 카테고리 CSV 경로입니다.")
    parser.add_argument("--tags", default=str(DEFAULT_TAGS), help="태그 매핑 CSV 경로입니다.")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="상품 카탈로그 CSV 경로입니다.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Markdown 리포트 저장 폴더입니다.")
    parser.add_argument("--list-keywords", action="store_true", help="샘플 데이터의 키워드 목록을 출력합니다.")
    return parser.parse_args(argv)


def run_cli(argv: list[str]) -> int:
    args = parse_cli_args(argv)
    signals_path = Path(args.signals)

    if args.list_keywords:
        payload = load_trend_signals(signals_path)
        print("사용 가능한 샘플 키워드:")
        for keyword in available_keywords(payload):
            print(f"- {keyword}")
        return 0

    keyword = args.keyword_option or args.keyword_arg
    if not keyword:
        print("오류: 평가할 키워드를 입력해주세요. 예: python main.py \"발레코어\"", file=sys.stderr)
        return 2

    result = build_trend_report(
        keyword=keyword,
        signals_path=signals_path,
        categories_path=Path(args.categories),
        tags_path=Path(args.tags),
        catalog_path=Path(args.catalog),
        output_dir=Path(args.output_dir),
    )

    score = result["score_result"]["total_score"]
    band = result["score_result"]["band"]
    print(f"키워드: {keyword}")
    print(f"총점: {score}/100점 ({band})")
    print(f"리포트 저장 경로: {result['output_path']}")
    return 0


def mcp_response(message_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> str:
    response: dict[str, Any] = {"jsonrpc": "2.0", "id": message_id}
    if error is not None:
        response["error"] = error
    else:
        response["result"] = result
    return json.dumps(response, ensure_ascii=False)


def run_mcp_server() -> int:
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        method = message.get("method")
        message_id = message.get("id")

        if method == "initialize":
            print(
                mcp_response(
                    message_id,
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "trend-signal-validator",
                            "version": "0.1.0",
                        },
                    },
                ),
                flush=True,
            )
        elif method == "tools/list":
            print(
                mcp_response(
                    message_id,
                    {
                        "tools": [
                            {
                                "name": "generate_trend_report",
                                "description": "키워드의 트렌드 점수와 무신사 연결성 리포트를 생성합니다.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "keyword": {
                                            "type": "string",
                                            "description": "평가할 트렌드 키워드",
                                        }
                                    },
                                    "required": ["keyword"],
                                },
                            }
                        ]
                    },
                ),
                flush=True,
            )
        elif method == "tools/call":
            params = message.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            if name != "generate_trend_report":
                print(
                    mcp_response(
                        message_id,
                        error={"code": -32601, "message": "알 수 없는 도구입니다."},
                    ),
                    flush=True,
                )
                continue
            keyword = str(arguments.get("keyword", "")).strip()
            if not keyword:
                print(
                    mcp_response(
                        message_id,
                        error={"code": -32602, "message": "keyword 값이 필요합니다."},
                    ),
                    flush=True,
                )
                continue
            try:
                result = build_trend_report(keyword)
                text = (
                    f"{keyword} 리포트를 생성했습니다.\n"
                    f"총점: {result['score_result']['total_score']}/100점 "
                    f"({result['score_result']['band']})\n"
                    f"저장 경로: {result['output_path']}"
                )
                print(
                    mcp_response(
                        message_id,
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": text,
                                }
                            ]
                        },
                    ),
                    flush=True,
                )
            except Exception as exc:
                print(
                    mcp_response(
                        message_id,
                        error={"code": -32000, "message": f"리포트 생성 실패: {exc}"},
                    ),
                    flush=True,
                )
        elif message_id is not None:
            print(
                mcp_response(
                    message_id,
                    error={"code": -32601, "message": "지원하지 않는 MCP 메서드입니다."},
                ),
                flush=True,
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "mcp":
        return run_mcp_server()
    return run_cli(argv)


if __name__ == "__main__":
    raise SystemExit(main())
