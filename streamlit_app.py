from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError

import streamlit as st

from exchange import CURRENCIES, fetch_rate, format_number, parse_question


st.set_page_config(page_title="환율 조회", page_icon=":material/currency_exchange:")
st.html(Path(__file__).with_name("style.css"))

EXAMPLES = (
    "100달러는 원화로 얼마야?",
    "1유로는 엔화로 얼마야?",
    "3만원을 USD로 바꿔 줘",
)
get_rate = st.cache_data(ttl=300, max_entries=225, show_spinner=False)(fetch_rate)


def answer(question):
    try:
        amount, base, quote = parse_question(question)
    except ValueError as error:
        return {"notice": str(error)}

    if base == quote:
        return {"notice": f"두 통화가 {base}로 같아요. 환산 금액은 {format_number(amount, 6)} {base}입니다."}

    try:
        rate, rate_date = get_rate(base, quote)
    except HTTPError as error:
        if error.code in (404, 422):
            return {"error": f"{base}에서 {quote}로 바꾸는 기준 환율이 없습니다. 다른 통화를 입력해 주세요."}
        return {"error": "환율 서버가 응답하지 않았어요. 잠시 후 다시 시도해 주세요."}
    except (OSError, ValueError, KeyError, TypeError, InvalidOperation):
        return {"error": "환율을 불러오지 못했어요. 잠시 후 다시 시도해 주세요."}

    converted = amount * rate
    places = 2 if converted >= Decimal("0.01") else 8
    return {
        "base": base,
        "quote": quote,
        "amount": format_number(amount, 6),
        "converted": format_number(converted, places),
        "rate": format_number(rate, 10),
        "date": rate_date.isoformat(),
    }


def show_answer(result):
    if "error" in result:
        st.error(result["error"])
    elif "notice" in result:
        st.write(result["notice"])
    else:
        # The interpolated values are formatted numbers, supported codes, and an ISO date.
        st.html(
            f"""
            <div class="conversion">
              <div class="conversion-from">{result["amount"]} {result["base"]}</div>
              <div class="conversion-to">
                <strong>{result["converted"]}</strong><span>{result["quote"]}</span>
              </div>
              <dl>
                <div><dt>적용 환율</dt>
                  <dd>1 {result["base"]} = {result["rate"]} {result["quote"]}</dd></div>
                <div><dt>환율 기준일</dt><dd>{result["date"]}</dd></div>
              </dl>
            </div>
            """
        )


st.title("환율 조회")
st.markdown("바꿀 금액과 두 통화를 적으면 최신 일별 기준 환율로 계산해 드려요.")

st.caption("예시 질문")
example_query = None
with st.container(horizontal=True, gap="small", key="examples"):
    for example in EXAMPLES:
        if st.button(example):
            example_query = example

with st.expander("지원 통화"):
    st.write(" · ".join(f"{names[0]} ({code})" for code, names in CURRENCIES.items()))
    st.caption("금액을 생략하면 기준 통화 1단위의 환율을 조회합니다.")

st.caption("데이터 출처 · [Frankfurter 일별 기준 환율](https://frankfurter.dev/)")

history = st.session_state.setdefault("history", [])
for question, result in history:
    with st.chat_message("user"):
        st.text(question)
    with st.chat_message("assistant", avatar=":material/currency_exchange:"):
        show_answer(result)

typed_query = st.chat_input("금액과 통화를 입력하세요", max_chars=160)
query = (example_query or typed_query or "").strip()
if query:
    with st.chat_message("user"):
        st.text(query)
    with st.chat_message("assistant", avatar=":material/currency_exchange:"):
        with st.spinner("기준 환율을 조회하고 있어요…"):
            result = answer(query)
        show_answer(result)
    history.append((query, result))
