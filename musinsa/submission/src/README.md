# 트렌드 신호 검증기

무신사 트렌드 키워드의 실행 가능성을 100점 만점으로 평가하고 Markdown 리포트를 생성하는 Codex 플러그인 MVP입니다. 실제 외부 API나 API 키를 사용하지 않고 `data/sample_trend_signals.json`의 mock 공개 신호 데이터를 읽어 동작합니다.

## 주요 기능

- 검색성, 소셜 확산성, 이미지·스타일 확산성, 브랜드 쇼 신호, 무신사 카테고리 연결성을 종합 점수화합니다.
- 무신사 카테고리·태그·상품 샘플 데이터를 바탕으로 추천 카테고리와 추천 태그를 생성합니다.
- 점수 결과, 근거 카드, 실행 액션을 포함한 Markdown 리포트를 `output/{keyword}_trend_report.md`에 저장합니다.
- Python 표준 라이브러리만 사용합니다.

## 파일 구조

```text
.codex-plugin/plugin.json
.mcp.json
skills/trend-signal-validator/SKILL.md
main.py
scorer.py
mapper.py
report_generator.py
data/sample_trend_signals.json
data/sample_external_signals.csv
data/sample_musinsa_categories.csv
data/sample_musinsa_tags.csv
data/sample_musinsa_catalog.csv
```

## 실행 방법

Python 3.10 이상이 설치된 환경에서 실행합니다.

```bash
python main.py "발레코어"
```

또는 옵션으로 키워드를 전달할 수 있습니다.

```bash
python main.py --keyword "고프코어"
```

샘플 데이터에 포함된 키워드는 다음 명령으로 확인합니다.

```bash
python main.py --list-keywords
```

## 샘플 실행 예시

```bash
$ python main.py "발레코어"
키워드: 발레코어
총점: 86.0/100점 (강한 실행 후보)
리포트 저장 경로: .../output/발레코어_trend_report.md
```

생성된 리포트에는 다음 내용이 포함됩니다.

- 100점 만점 총점과 평가 항목별 점수
- 검색성, 소셜 확산성, 이미지·스타일 확산성, 브랜드 쇼 신호, 카테고리 연결성 근거
- 추천 카테고리와 추천 태그
- 기획전, 태그 정비, 검색어 실험 등 실행 액션

## MCP 사용

`.mcp.json`은 `main.py mcp`를 stdio MCP 서버로 실행하도록 설정되어 있습니다. MCP 도구 이름은 `generate_trend_report`이며, 입력값은 `keyword` 하나입니다.

## 주의사항

- 이 MVP의 데이터는 실제 무신사 내부 데이터나 외부 API 응답이 아니라, 실행 가능한 데모를 위한 샘플입니다.
- 외부 API 키, 네트워크 호출, 비표준 Python 패키지는 사용하지 않습니다.
