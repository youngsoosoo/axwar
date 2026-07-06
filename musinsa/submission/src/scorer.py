from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScoreBand:
    label: str
    description: str


WEIGHTS = {
    "search": 0.25,
    "social": 0.20,
    "style": 0.20,
    "brand_show": 0.15,
    "category_connection": 0.20,
}


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def normalize_growth(value: float, strong_growth: float = 60.0) -> float:
    if value <= 0:
        return 0.0
    return clamp((value / strong_growth) * 100.0)


def normalize_count(value: float, strong_count: float) -> float:
    if value <= 0:
        return 0.0
    return clamp((value / strong_count) * 100.0)


def calculate_component_scores(
    signal: dict[str, Any],
    category_connection_score: float,
) -> dict[str, float]:
    search_index = float(signal.get("search_index", 0))
    search_growth = float(signal.get("search_growth", 0))
    social_mentions = float(signal.get("social_mentions", 0))
    social_growth = float(signal.get("social_growth", 0))
    image_posts = float(signal.get("image_posts", 0))
    style_growth = float(signal.get("style_growth", 0))
    brand_show_count = float(signal.get("brand_show_count", 0))
    brand_show_mentions = float(signal.get("brand_show_mentions", 0))

    search = (clamp(search_index) * 0.7) + (normalize_growth(search_growth) * 0.3)
    social = (normalize_count(social_mentions, 15000) * 0.55) + (
        normalize_growth(social_growth) * 0.45
    )
    style = (normalize_count(image_posts, 8000) * 0.55) + (
        normalize_growth(style_growth) * 0.45
    )
    brand_show = (normalize_count(brand_show_count, 8) * 0.65) + (
        normalize_count(brand_show_mentions, 12) * 0.35
    )

    return {
        "search": round(clamp(search), 1),
        "social": round(clamp(social), 1),
        "style": round(clamp(style), 1),
        "brand_show": round(clamp(brand_show), 1),
        "category_connection": round(clamp(category_connection_score), 1),
    }


def calculate_total_score(component_scores: dict[str, float]) -> float:
    total = 0.0
    for key, weight in WEIGHTS.items():
        total += component_scores.get(key, 0.0) * weight
    return round(clamp(total), 1)


def score_band(total_score: float) -> ScoreBand:
    if total_score >= 80:
        return ScoreBand("확장 추천", "검색·확산·상품 연결성이 모두 높아 즉시 기획 검토가 가능합니다.")
    if total_score >= 65:
        return ScoreBand("테스트 권장", "신호가 충분하므로 카테고리와 태그를 보강해 실험할 만합니다.")
    if total_score >= 50:
        return ScoreBand("관찰 필요", "일부 신호는 있으나 소규모 콘텐츠나 검색어 실험부터 권장합니다.")
    return ScoreBand("보류", "현재 샘플 기준 신호가 약해 추가 근거 확보가 필요합니다.")


def build_score_result(
    signal: dict[str, Any],
    category_connection_score: float,
) -> dict[str, Any]:
    component_scores = calculate_component_scores(signal, category_connection_score)
    total_score = calculate_total_score(component_scores)
    band = score_band(total_score)
    return {
        "total_score": total_score,
        "band": band.label,
        "band_description": band.description,
        "component_scores": component_scores,
        "weights": WEIGHTS,
    }
