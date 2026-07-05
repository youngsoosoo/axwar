---
name: trend-signal-validator
description: 무신사 패션 트렌드 키워드의 검색성, 소셜 확산성, 이미지·스타일 확산성, 브랜드 쇼 신호, 무신사 카테고리 연결성을 검증하고 Markdown 리포트를 생성할 때 사용합니다. 사용자가 트렌드 키워드 점수화, 추천 카테고리·태그 매핑, 실행 액션 도출, sample_trend_signals.json 기반 MVP 실행을 요청하면 이 스킬을 사용합니다.
---

# 트렌드 신호 검증기

이 스킬은 공개 트렌드 신호를 모사한 mock 데이터와 무신사 카테고리·태그·상품 샘플 데이터를 연결해 키워드별 실행 가능성을 평가한다.

## 기본 절차

1. 사용자가 평가할 한국어 또는 영어 키워드를 확인한다.
2. 플러그인 루트에서 `python main.py "<키워드>"`를 실행한다.
3. 생성된 `output/{keyword}_trend_report.md` 리포트를 확인한다.
4. 사용자에게 총점, 핵심 근거, 추천 카테고리, 추천 태그, 다음 액션을 요약한다.

## 입력 데이터

- `data/sample_trend_signals.json`: CLI가 기본으로 읽는 mock 공개 트렌드 신호 데이터
- `data/sample_external_signals.csv`: 외부 공개 신호를 CSV 형태로 검토하기 위한 샘플 데이터
- `data/sample_musinsa_categories.csv`: 무신사 카테고리 구조를 단순화한 샘플 데이터
- `data/sample_musinsa_tags.csv`: 추천 태그 매핑용 샘플 데이터
- `data/sample_musinsa_catalog.csv`: 상품 연결성 계산용 샘플 상품 데이터

## 점수 해석

- 80점 이상: 바로 기획 검토 가능한 강한 트렌드 신호
- 65점 이상 80점 미만: 카테고리·태그 보강 후 테스트할 만한 신호
- 50점 이상 65점 미만: 소규모 콘텐츠 또는 검색어 실험에 적합
- 50점 미만: 근거가 약하므로 추가 데이터 확인 필요

## 실행 예시

```bash
python main.py "발레코어"
python main.py --keyword "고프코어"
python main.py --list-keywords
```

## 작업 원칙

- 실제 API 키가 필요한 외부 API를 호출하지 않는다.
- Python 표준 라이브러리만 사용한다.
- 리포트 내용과 사용자 설명은 한국어로 작성한다.
- 없는 키워드는 낮은 기본 점수로 처리하되, 사용 가능한 샘플 키워드를 함께 안내한다.
- 결과 파일 경로와 생성 여부를 반드시 사용자에게 알려준다.
