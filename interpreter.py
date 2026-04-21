from config import (
    CAPE_THRESHOLDS, ECY_THRESHOLDS, BUFFETT_THRESHOLDS,
    YIELD_CURVE_THRESHOLDS, VIX_THRESHOLDS,
    FG_STOCK_THRESHOLDS, FG_CRYPTO_THRESHOLDS,
)


def _interpret(value: float, thresholds: list) -> tuple[int, str, str]:
    for ceiling, score, emoji, desc in thresholds:
        if value <= ceiling:
            return score, emoji, desc
    last = thresholds[-1]
    return last[1], last[2], last[3]


def interpret_cape(v: float) -> tuple[int, str, str]:
    return _interpret(v, CAPE_THRESHOLDS)

def interpret_ecy(v: float) -> tuple[int, str, str]:
    return _interpret(v, ECY_THRESHOLDS)

def interpret_buffett(v: float) -> tuple[int, str, str]:
    return _interpret(v, BUFFETT_THRESHOLDS)

def interpret_yield_curve(v: float) -> tuple[int, str, str]:
    return _interpret(v, YIELD_CURVE_THRESHOLDS)

def interpret_vix(v: float) -> tuple[int, str, str]:
    return _interpret(v, VIX_THRESHOLDS)

def interpret_fg_stock(v: int) -> tuple[int, str, str]:
    return _interpret(v, FG_STOCK_THRESHOLDS)

def interpret_fg_crypto(v: int) -> tuple[int, str, str]:
    return _interpret(v, FG_CRYPTO_THRESHOLDS)


MATRIX = {
    ("expensive", "fear"):    ("혼조 \u00b7 분할매수", "\U0001f7e1",
        "\u201c비싼데 겁도 먹고 있다\u201d = 혼조 구간\n"
        "\u2022 비싸서 올인은 위험하지만\n"
        "\u2022 공포가 높아서 단기 바닥은 가까울 수 있음\n"
        "\u2022 역사적으로 이런 조합에서는 \u2018조금씩 분할매수\u2019가 최선"),
    ("expensive", "neutral"): ("고점 주의", "\U0001f7e0",
        "\u201c비싼데 아무도 안 무서워한다\u201d = 위험 구간\n"
        "\u2022 시장이 자만 중 \u2014 작은 충격에도 급락 가능\n"
        "\u2022 신규 진입은 최소화, 현금\u00b7채권 비중 유지\n"
        "\u2022 VIX 35+ 올 때까지 기다리는 게 유리"),
    ("expensive", "greed"):   ("\U0001f6a8 도망쳐", "\U0001f534",
        "\u201c비싸고 다들 탐욕에 빠져있다\u201d = 가장 위험\n"
        "\u2022 역사적 고점 근처에서 흔히 보이는 조합\n"
        "\u2022 레버리지\u00b7추격매수 절대 금지\n"
        "\u2022 현금 확보 + 리스크 축소가 급선무"),
    ("normal", "fear"):       ("기회 탐색", "\U0001f7e2",
        "\u201c적당한 가격에 공포\u201d = 기회가 다가오는 중\n"
        "\u2022 분할매수 시작해도 괜찮은 구간\n"
        "\u2022 공포가 더 커지면 비중 확대 고려"),
    ("normal", "neutral"):    ("평온 \u00b7 유지", "\U0001f7e2",
        "\u201c적당한 가격, 적당한 심리\u201d = 평온\n"
        "\u2022 기존 포트폴리오 유지\n"
        "\u2022 특별히 사거나 팔 이유 없음"),
    ("normal", "greed"):      ("욕심 자제", "\U0001f7e1",
        "\u201c가격은 괜찮지만 분위기가 과열\u201d\n"
        "\u2022 추격매수 자제\n"
        "\u2022 수익 일부 실현 고려"),
    ("cheap", "fear"):        ("\U0001f3af 인생 매수", "\U0001f7e2",
        "\u201c싸고 다들 겁먹었다\u201d = 역사적 최고 매수 타이밍\n"
        "\u2022 2009, 2020.3 같은 구간\n"
        "\u2022 용기 내서 적극 매수할 때\n"
        "\u2022 이때 산 사람이 부자가 됨"),
    ("cheap", "neutral"):     ("적극 매수", "\U0001f7e2",
        "\u201c싸고 분위기도 안정\u201d = 좋은 진입점\n"
        "\u2022 장기 투자 시작하기 좋은 때"),
    ("cheap", "greed"):       ("회복 초기", "\U0001f7e1",
        "\u201c싸지만 분위기는 회복 중\u201d\n"
        "\u2022 이미 반등이 시작된 구간\n"
        "\u2022 기존 포지션 유지, 추격은 자제"),
}


def _bucket(scores: list[int]) -> str:
    avg = sum(scores) / len(scores)
    if avg >= 3.8:
        return "expensive"
    if avg <= 2.2:
        return "cheap"
    return "normal"


def _sentiment_bucket(scores: list[int]) -> str:
    avg = sum(scores) / len(scores)
    if avg >= 3.8:
        return "greed"
    if avg <= 2.2:
        return "fear"
    return "neutral"


VALUATION_LABEL = {"expensive": "\U0001f4b8 비쌈", "normal": "\U0001f610 보통", "cheap": "\U0001f7e2 저렴"}
SENTIMENT_LABEL = {"fear": "\U0001f628 공포", "neutral": "\U0001f610 보통", "greed": "\U0001f911 탐욕"}


def diagnose(data: dict) -> dict:
    val_scores = []
    sent_scores = []
    indicators = {}

    if data.get("cape") is not None:
        s, e, d = interpret_cape(data["cape"])
        val_scores.append(s)
        indicators["cape"] = {"value": data["cape"], "fmt": f"{data['cape']:.1f}", "score": s, "emoji": e, "desc": d}

    if data.get("ecy") is not None:
        s, e, d = interpret_ecy(data["ecy"])
        val_scores.append(s)
        indicators["ecy"] = {"value": data["ecy"], "fmt": f"{data['ecy']:+.2f}%", "score": s, "emoji": e, "desc": d}

    if data.get("buffett") is not None:
        s, e, d = interpret_buffett(data["buffett"])
        val_scores.append(s)
        indicators["buffett"] = {"value": data["buffett"], "fmt": f"{data['buffett']:.0f}%", "score": s, "emoji": e, "desc": d}

    if data.get("yield_curve") is not None:
        s, e, d = interpret_yield_curve(data["yield_curve"])
        indicators["yield_curve"] = {"value": data["yield_curve"], "fmt": f"{data['yield_curve']:+.2f}%", "score": s, "emoji": e, "desc": d}

    if data.get("rate_10y") is not None:
        indicators["rate_10y"] = {"value": data["rate_10y"], "fmt": f"{data['rate_10y']:.2f}%"}

    if data.get("vix") is not None:
        s, e, d = interpret_vix(data["vix"])
        sent_scores.append(s)
        indicators["vix"] = {"value": data["vix"], "fmt": f"{data['vix']:.1f}", "score": s, "emoji": e, "desc": d}

    if data.get("cnn_fg") is not None:
        score_val, label = data["cnn_fg"]
        s, e, d = interpret_fg_stock(score_val)
        sent_scores.append(s)
        indicators["cnn_fg"] = {"value": score_val, "fmt": f"{score_val} ({label})", "score": s, "emoji": e, "desc": d}

    if data.get("crypto_fg") is not None:
        score_val, label = data["crypto_fg"]
        s, e, d = interpret_fg_crypto(score_val)
        sent_scores.append(s)
        indicators["crypto_fg"] = {"value": score_val, "fmt": f"{score_val} ({label})", "score": s, "emoji": e, "desc": d}

    val_bucket = _bucket(val_scores) if val_scores else "normal"
    sent_bucket = _sentiment_bucket(sent_scores) if sent_scores else "neutral"

    matrix_key = (val_bucket, sent_bucket)
    matrix_label, matrix_emoji, matrix_detail = MATRIX.get(matrix_key, ("판단 불가", "\u2753", "데이터 부족"))

    marks = calc_marks_temp(data)

    return {
        "indicators": indicators,
        "valuation": val_bucket,
        "sentiment": sent_bucket,
        "valuation_label": VALUATION_LABEL.get(val_bucket, "?"),
        "sentiment_label": SENTIMENT_LABEL.get(sent_bucket, "?"),
        "matrix_label": matrix_label,
        "matrix_emoji": matrix_emoji,
        "matrix_detail": matrix_detail,
        "marks": marks,
    }


def _norm(value: float, cold: float, hot: float) -> float:
    return max(0.0, min(100.0, (value - cold) / (hot - cold) * 100))


MARKS_LEVELS = [
    (20, "\u2744\ufe0f", "극단적 공포", "막스라면 \"지금 공격적으로 사라\""),
    (40, "\U0001f7e2", "차가움", "좋은 기회가 보이는 구간"),
    (60, "\U0001f7e1", "미지근", "평범, 선별적 투자"),
    (80, "\U0001f7e0", "\ub728\uac70\uc6c0", "\uc870\uc2ec! \ub9ac\uc2a4\ud06c \uc904\uc5ec\ub77c"),
    (100, "\U0001f534", "과열", "막스라면 \"방어 모드 전환\""),
]


def calc_marks_temp(data: dict) -> dict | None:
    components = {}

    if data.get("cape") is not None:
        components["CAPE"] = _norm(data["cape"], 10, 45)

    if data.get("vix") is not None:
        components["VIX"] = _norm(data["vix"], 45, 10)

    if data.get("cnn_fg") is not None:
        score_val = data["cnn_fg"][0] if isinstance(data["cnn_fg"], tuple) else data["cnn_fg"]
        components["F&G"] = float(score_val)

    if data.get("credit_spread") is not None:
        components["신용"] = _norm(data["credit_spread"], 10, 3)

    if not components:
        return None

    temp = sum(components.values()) / len(components)
    temp = round(temp)

    emoji = "\U0001f534"
    level = "과열"
    advice = "막스라면 \"방어 모드 전환\""
    for ceiling, e, lv, adv in MARKS_LEVELS:
        if temp <= ceiling:
            emoji, level, advice = e, lv, adv
            break

    bar_pos = max(0, min(20, round(temp / 5)))
    bar = "\u2744\ufe0f " + "\u2501" * bar_pos + "\u25cf" + "\u2501" * (20 - bar_pos) + " \U0001f525"

    return {
        "temp": temp,
        "emoji": emoji,
        "level": level,
        "advice": advice,
        "bar": bar,
        "components": components,
    }
