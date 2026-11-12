# 환율 조회

Streamlit과 Frankfurter v2 API를 사용하는 한국어 환율 챗봇입니다. `100달러는 원화로 얼마야?`처럼 입력하면 환산 금액, 적용 환율, 기준일을 보여줍니다. 통화는 바꿀 통화부터 입력하고, 금액을 생략하면 1단위로 계산합니다.

[Frankfurter](https://frankfurter.dev/)의 공개 API는 일별 기준 환율을 제공하며 API 키가 필요 없습니다.

## 로컬에서 실행

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Streamlit Community Cloud

[Streamlit Community Cloud](https://share.streamlit.io/)에서 저장소 `larklaon/exch_app_proj`, 브랜치 `main`, 앱 파일 `streamlit_app.py`를 선택합니다.
