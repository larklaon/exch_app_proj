import json
import re
import unicodedata
from datetime import date
from decimal import Decimal
from urllib.request import urlopen


CURRENCIES = {
    "USD": ("미국 달러", "미 달러", "달러", "불", "$"),
    "KRW": ("한국 원", "원화", "원", "₩"),
    "EUR": ("유로", "€"),
    "JPY": ("일본 엔", "엔화", "엔", "¥"),
    "GBP": ("영국 파운드", "파운드", "£"),
    "CNY": ("중국 위안", "위안화", "위안"),
    "AUD": ("호주 달러", "호주달러"),
    "CAD": ("캐나다 달러", "캐나다달러"),
    "CHF": ("스위스 프랑", "프랑"),
    "HKD": ("홍콩 달러", "홍콩달러"),
    "SGD": ("싱가포르 달러", "싱가포르달러"),
    "NZD": ("뉴질랜드 달러", "뉴질랜드달러"),
    "THB": ("태국 바트", "바트"),
    "VND": ("베트남 동", "동"),
    "TWD": ("대만 달러", "대만달러"),
}
ALIASES = {
    alias: code for code, names in CURRENCIES.items() for alias in (code, *names)
}


def currency_pattern(alias):
    escaped = re.escape(alias)
    if alias in CURRENCIES:
        return rf"(?<![a-z]){escaped}(?![a-z])"
    if len(alias) == 1 and alias.isalpha():
        return rf"(?:(?<![가-힣])|(?<=[천만억])){escaped}(?=$|[^가-힣]|[은는이를을과로에당]|으로)"
    return escaped


CURRENCY_PATTERN = re.compile(
    "|".join(currency_pattern(alias) for alias in sorted(ALIASES, key=len, reverse=True)),
    re.IGNORECASE,
)
NUMBER_PATTERN = re.compile(r"[+-]?(?:[0-9][0-9,.]*|\.[0-9]+)")
MULTIPLIERS = {"천": 1_000, "만": 10_000, "억": 100_000_000}


def parse_question(question):
    normalized = unicodedata.normalize("NFKC", question).replace("−", "-")
    normalized = " ".join(normalized.split())
    currencies = list(CURRENCY_PATTERN.finditer(normalized))
    if len(currencies) != 2:
        raise ValueError("바꿀 통화와 받을 통화를 순서대로 적어 주세요. 예) 100달러는 원화로 얼마야?")

    numbers = list(NUMBER_PATTERN.finditer(normalized))
    if len(numbers) > 1:
        raise ValueError("한 번에 금액 하나만 입력해 주세요.")

    amount = Decimal(1)
    if numbers:
        number = numbers[0]
        value = number.group().removesuffix(".")
        if not re.fullmatch(
            r"[+]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,6})?|[+]?\.[0-9]{1,6}",
            value,
        ):
            raise ValueError("금액을 0 이상의 숫자로 적어 주세요. 예) 1,250.50 USD를 KRW로")
        if len(value) > 20:
            raise ValueError("금액을 1조 미만으로 적어 주세요.")
        amount = Decimal(value.replace(",", ""))
        after_number = normalized[number.end():].lstrip()
        if after_number[:1] in MULTIPLIERS:
            amount *= MULTIPLIERS[after_number[0]]
        if amount >= 1_000_000_000_000:
            raise ValueError("금액을 1조 미만으로 적어 주세요.")

    base, quote = (ALIASES[match.group().upper()] for match in currencies)
    return amount, base, quote


def fetch_rate(base, quote):
    with urlopen(f"https://api.frankfurter.dev/v2/rate/{base}/{quote}", timeout=8) as response:
        data = json.load(response, parse_float=Decimal)

    if data["base"] != base or data["quote"] != quote:
        raise ValueError("Unexpected currency pair")
    rate = Decimal(data["rate"])
    if not rate.is_finite() or rate <= 0:
        raise ValueError("Invalid exchange rate")
    return rate, date.fromisoformat(data["date"])


def format_number(number, places):
    formatted = f"{number:,.{places}f}"
    return formatted.rstrip("0").rstrip(".") if places else formatted
