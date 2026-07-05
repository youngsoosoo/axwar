from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


COMPONENT_LABELS = {
    "search": "검색성",
    "social": "소셜 확산성",
    "style": "이미지·스타일 확산성",
    "brand_show": "브랜드 쇼 신호",
    "category_connection": "무신사 카테고리 연결성",
}


def safe_filename(keyword: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in ("-", "_", " ") else "_" for char in keyword)
    cleaned = "_".join(cleaned.strip().split())
    return cleaned or "trend"


def format_reason_list(reasons: list[str]) -> str:
    if not reasons:
        return "근거 없음"
    return ", ".join(reasons)


def build_action_items(total_score: float, categories: list[dict[str, Any]], tags: list[dict[str, Any]]) -> list[str]:
    top_category = categories[0]["path"] if categories else "연관 카테고리"
    top_tags = ", ".join(f"#{tag['tag_name']}" for tag in tags[:3]) if tags else "핵심 태그"

    if total_score >= 80:
        return [
            f"{top_category} 중심으로 1차 기획전 또는 스타일 큐레이션을 구성합니다.",
            f"{top_tags}를 상품 태그와 검색 키워드 후보에 반영합니다.",
            "상위 상품 20개를 수동 검수해 대표 이미지 톤과 가격대를 맞춥니다.",
            "트렌드 콘텐츠, 검색 광고, 앱 푸시를 같은 주차에 묶어 초기 반응을 확인합니다.",
        ]
    if total_score >= 65:
        return [
            f"{top_category}에서 소규모 컬렉션을 구성해 클릭률과 전환율을 확인합니다.",
            f"{top_tags}를 중심으로 검색어 실험과 태그 정비를 진행합니다.",
            "관련 상품 수와 재고 안정성을 확인한 뒤 노출 지면을 확장합니다.",
        ]
    if total_score >= 50:
        return [
            "콘텐츠형 테스트로 시작해 저장, 공유, 검색 유입 변화를 관찰합니다.",
            f"{top_tags} 후보를 낮은 우선순위 태그로 등록하고 반응을 확인합니다.",
            "추가 외부 신호가 쌓이면 카테고리 확장을 재평가합니다.",
        ]
    return [
        "현재는 정식 기획보다 모니터링 키워드로 유지합니다.",
        "검색량, 스타일 이미지, 브랜드 쇼 언급이 추가로 확인될 때 다시 점수화합니다.",
        "샘플 데이터에 포함된 키워드로 비교 평가해 기준점을 잡습니다.",
    ]


def generate_markdown_report(
    keyword: str,
    signal: dict[str, Any],
    score_result: dict[str, Any],
    mapping_result: dict[str, Any],
    source_files: dict[str, str],
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_score = score_result["total_score"]
    categories = mapping_result["recommended_categories"]
    tags = mapping_result["recommended_tags"]
    action_items = build_action_items(total_score, categories, tags)

    lines: list[str] = [
        f"# {keyword} 트렌드 신호 검증 리포트",
        "",
        f"- 생성 시각: {generated_at}",
        f"- 총점: **{total_score}/100점**",
        f"- 판정: **{score_result['band']}**",
        f"- 해석: {score_result['band_description']}",
        "",
        "## 점수 요약",
        "",
        "| 평가 항목 | 점수 | 가중치 |",
        "| --- | ---: | ---: |",
    ]

    for key, score in score_result["component_scores"].items():
        weight = score_result["weights"][key] * 100
        lines.append(f"| {COMPONENT_LABELS[key]} | {score:.1f} | {weight:.0f}% |")

    lines.extend(
        [
            "",
            "## 근거 카드",
            "",
            f"- 검색성: 검색 지수 {signal.get('search_index', 0)}, 검색 성장률 {signal.get('search_growth', 0)}%",
            f"- 소셜 확산성: 소셜 언급량 {signal.get('social_mentions', 0):,}건, 성장률 {signal.get('social_growth', 0)}%",
            f"- 이미지·스타일 확산성: 스타일 이미지 {signal.get('image_posts', 0):,}건, 성장률 {signal.get('style_growth', 0)}%",
            f"- 브랜드 쇼 신호: 쇼/룩북 포착 {signal.get('brand_show_count', 0)}건, 브랜드 언급 {signal.get('brand_show_mentions', 0)}건",
            f"- 무신사 연결성: 카테고리 연결 점수 {mapping_result['category_connection_score']:.1f}점",
            "",
        ]
    )

    evidence_items = signal.get("evidence", [])
    if evidence_items:
        lines.extend(["### 세부 근거", ""])
        for item in evidence_items:
            lines.append(f"- **{item.get('title', '근거')}**: {item.get('detail', '')}")
        lines.append("")

    lines.extend(["## 추천 카테고리", ""])
    if categories:
        lines.extend(["| 순위 | 카테고리 | 연결 점수 | 매칭 상품 수 | 근거 |", "| ---: | --- | ---: | ---: | --- |"])
        for index, category in enumerate(categories, start=1):
            lines.append(
                f"| {index} | {category['path']} | {category['score']} | "
                f"{category['matched_products']} | {format_reason_list(category['reasons'])} |"
            )
    else:
        lines.append("- 추천 가능한 카테고리가 없습니다.")

    lines.extend(["", "## 추천 태그", ""])
    if tags:
        lines.extend(["| 순위 | 태그 | 점수 | 카테고리 힌트 | 근거 |", "| ---: | --- | ---: | --- | --- |"])
        for index, tag in enumerate(tags, start=1):
            lines.append(
                f"| {index} | #{tag['tag_name']} | {tag['score']} | "
                f"{tag['category_hint']} | {format_reason_list(tag['reasons'])} |"
            )
    else:
        lines.append("- 추천 가능한 태그가 없습니다.")

    lines.extend(["", "## 실행 액션", ""])
    for index, action in enumerate(action_items, start=1):
        lines.append(f"{index}. {action}")

    lines.extend(["", "## 사용 데이터", ""])
    for label, path in source_files.items():
        lines.append(f"- {label}: `{path}`")

    lines.append("")
    return "\n".join(lines)


def write_report(output_dir: Path, keyword: str, markdown: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(keyword)}_trend_report.md"
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
