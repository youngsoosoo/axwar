from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def split_multi_value(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[|,]", value) if item.strip()]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_trend_signals(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict) or "signals" not in payload:
        raise ValueError("sample_trend_signals.json 형식이 올바르지 않습니다.")
    return payload


def available_keywords(payload: dict[str, Any]) -> list[str]:
    return [str(item.get("keyword", "")) for item in payload.get("signals", []) if item.get("keyword")]


def find_signal(keyword: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized_keyword = normalize_text(keyword)
    for signal in payload.get("signals", []):
        names = [signal.get("keyword", "")]
        names.extend(signal.get("aliases", []))
        if normalized_keyword in {normalize_text(str(name)) for name in names}:
            return dict(signal)

    for signal in payload.get("signals", []):
        searchable = " ".join(
            [
                str(signal.get("keyword", "")),
                " ".join(str(alias) for alias in signal.get("aliases", [])),
                " ".join(str(tag) for tag in signal.get("related_tags", [])),
            ]
        )
        if normalized_keyword and normalized_keyword in normalize_text(searchable):
            return dict(signal)

    return {
        "keyword": keyword,
        "aliases": [],
        "search_index": 15,
        "search_growth": 0,
        "social_mentions": 300,
        "social_growth": 0,
        "image_posts": 120,
        "style_growth": 0,
        "brand_show_count": 0,
        "brand_show_mentions": 0,
        "related_categories": [],
        "related_tags": [],
        "evidence": [
            {
                "title": "샘플 데이터 미매칭",
                "detail": "입력 키워드와 정확히 일치하는 mock 공개 신호가 없어 낮은 기본값으로 평가했습니다.",
            }
        ],
    }


def recommend_categories(
    keyword: str,
    signal: dict[str, Any],
    categories: list[dict[str, str]],
    catalog: list[dict[str, str]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    normalized_keyword = normalize_text(keyword)
    related_categories = set(signal.get("related_categories", []))
    related_tags = {normalize_text(str(tag)) for tag in signal.get("related_tags", [])}
    category_scores: dict[str, dict[str, Any]] = {}

    for category in categories:
        category_id = category.get("category_id", "")
        keywords = {normalize_text(item) for item in split_multi_value(category.get("keywords"))}
        score = 0
        reasons: list[str] = []

        if category_id in related_categories:
            score += 45
            reasons.append("트렌드 신호의 연관 카테고리")
        if normalized_keyword in keywords:
            score += 30
            reasons.append("카테고리 키워드 직접 매칭")
        elif any(normalized_keyword in item or item in normalized_keyword for item in keywords):
            score += 18
            reasons.append("카테고리 키워드 부분 매칭")

        category_scores[category_id] = {
            "category_id": category_id,
            "path": " > ".join(
                part
                for part in [
                    category.get("depth1", ""),
                    category.get("depth2", ""),
                    category.get("depth3", ""),
                ]
                if part
            ),
            "score": score,
            "matched_products": 0,
            "reasons": reasons,
        }

    for product in catalog:
        category_id = product.get("category_id", "")
        if category_id not in category_scores:
            continue

        product_keywords = {
            normalize_text(item) for item in split_multi_value(product.get("keyword_hint"))
        }
        product_tags = {normalize_text(item) for item in split_multi_value(product.get("tags"))}
        product_score = 0

        if normalized_keyword in product_keywords:
            product_score += 18
        elif any(normalized_keyword in item or item in normalized_keyword for item in product_keywords):
            product_score += 10

        tag_overlap = len(product_tags & related_tags)
        product_score += min(tag_overlap * 6, 18)

        if product_score:
            category_scores[category_id]["score"] += product_score
            category_scores[category_id]["matched_products"] += 1
            if "상품·태그 연결성 확인" not in category_scores[category_id]["reasons"]:
                category_scores[category_id]["reasons"].append("상품·태그 연결성 확인")

    ranked = sorted(
        category_scores.values(),
        key=lambda item: (item["score"], item["matched_products"], item["path"]),
        reverse=True,
    )
    return [item for item in ranked if item["score"] > 0][:limit]


def recommend_tags(
    keyword: str,
    signal: dict[str, Any],
    tags: list[dict[str, str]],
    limit: int = 8,
) -> list[dict[str, Any]]:
    normalized_keyword = normalize_text(keyword)
    related_tags = {normalize_text(str(tag)) for tag in signal.get("related_tags", [])}
    ranked: list[dict[str, Any]] = []

    for tag in tags:
        aliases = {normalize_text(item) for item in split_multi_value(tag.get("aliases"))}
        tag_name = tag.get("tag_name", "")
        normalized_tag = normalize_text(tag_name)
        score = int(tag.get("weight", "50") or 50)
        reasons: list[str] = []

        if normalized_tag in related_tags or aliases & related_tags:
            score += 35
            reasons.append("트렌드 연관 태그")
        if normalized_keyword == normalized_tag or normalized_keyword in aliases:
            score += 30
            reasons.append("키워드 직접 매칭")
        elif normalized_keyword in normalized_tag or any(normalized_keyword in alias for alias in aliases):
            score += 15
            reasons.append("키워드 부분 매칭")

        if reasons:
            ranked.append(
                {
                    "tag_id": tag.get("tag_id", ""),
                    "tag_name": tag_name,
                    "score": min(score, 100),
                    "category_hint": tag.get("category_hint", ""),
                    "reasons": reasons,
                }
            )

    ranked.sort(key=lambda item: (item["score"], item["tag_name"]), reverse=True)
    return ranked[:limit]


def category_connection_score(recommended_categories: list[dict[str, Any]]) -> float:
    if not recommended_categories:
        return 10.0
    top_score = min(float(recommended_categories[0]["score"]), 100.0)
    matched_products = sum(int(item.get("matched_products", 0)) for item in recommended_categories)
    category_coverage = min(len(recommended_categories) * 8, 32)
    product_bonus = min(matched_products * 5, 25)
    return min(top_score * 0.55 + category_coverage + product_bonus, 100.0)


def build_mapping_result(
    keyword: str,
    signal: dict[str, Any],
    categories_path: Path,
    tags_path: Path,
    catalog_path: Path,
) -> dict[str, Any]:
    categories = load_csv(categories_path)
    tags = load_csv(tags_path)
    catalog = load_csv(catalog_path)
    category_matches = recommend_categories(keyword, signal, categories, catalog)
    tag_matches = recommend_tags(keyword, signal, tags)
    return {
        "recommended_categories": category_matches,
        "recommended_tags": tag_matches,
        "category_connection_score": round(category_connection_score(category_matches), 1),
    }
