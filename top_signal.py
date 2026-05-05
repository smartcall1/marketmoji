"""
Top Signal — BTC 사이클 꼭대기 감지 12개 지표 종합.
무료 공개 API만 사용, Termux/ARM 호환 (브라우저 불필요).
"""

import math
import asyncio
from datetime import datetime, timezone, timedelta

import httpx

_TIMEOUT = 30
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_HEADERS = {"User-Agent": _UA}

# ──────────────────────────────────────────────
# 지표 정의: threshold 도달 시 HIT (사이클 탑 경고)
# ──────────────────────────────────────────────
INDICATORS = [
    {"id": "mvrv", "name": "MVRV", "threshold": 3.7, "op": ">=", "cat": "On-Chain", "unit": ""},
    {"id": "nupl", "name": "NUPL", "threshold": 0.75, "op": ">=", "cat": "On-Chain", "unit": ""},
    {"id": "puell", "name": "Puell Multiple", "threshold": 4.0, "op": ">=", "cat": "On-Chain", "unit": ""},
    {"id": "pi_cycle", "name": "Pi Cycle Top", "threshold": 1.0, "op": ">=", "cat": "Cycle", "unit": ""},
    {"id": "dominance", "name": "BTC Dominance", "threshold": 45.0, "op": "<=", "cat": "Cycle", "unit": "%"},
    {"id": "mayer", "name": "Mayer Multiple", "threshold": 2.4, "op": ">=", "cat": "Cycle", "unit": ""},
    {"id": "log_growth", "name": "Log Growth", "threshold": 2.0, "op": ">=", "cat": "Cycle", "unit": "×"},
    {"id": "fear_greed", "name": "Fear & Greed", "threshold": 80, "op": ">=", "cat": "Sentiment", "unit": ""},
    {"id": "funding", "name": "Perp Funding", "threshold": 0.05, "op": ">=", "cat": "Derivatives", "unit": "%"},
    {"id": "exchange_inflow", "name": "Exchange Inflow", "threshold": 1.8, "op": ">=", "cat": "Flow", "unit": "×"},
    {"id": "etf_outflow", "name": "ETF Outflow", "threshold": 5, "op": ">=", "cat": "Flow", "unit": "일"},
    {"id": "ahr999", "name": "Ahr999", "threshold": 1.2, "op": ">=", "cat": "Cycle", "unit": ""},
]


# ──────────────────────────────────────────────
# HTTP 헬퍼
# ──────────────────────────────────────────────
async def _get(url: str, headers: dict | None = None, params: dict | None = None):
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=headers or _HEADERS, follow_redirects=True) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            return r
    except Exception:
        return None


# ──────────────────────────────────────────────
# 개별 데이터 소스 fetcher
# ──────────────────────────────────────────────

async def _fetch_coingecko_history(days: int = 365) -> list[float] | None:
    """CoinGecko에서 BTC 일별 종가 리스트 (oldest→newest)."""
    r = await _get(
        "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
        params={"vs_currency": "usd", "days": str(days), "interval": "daily"},
    )
    if not r:
        return None
    try:
        prices = r.json()["prices"]  # [[timestamp_ms, price], ...]
        return [p[1] for p in prices]
    except Exception:
        return None


async def _fetch_btc_dominance() -> float | None:
    r = await _get("https://api.coingecko.com/api/v3/global")
    if not r:
        return None
    try:
        return r.json()["data"]["market_cap_percentage"]["btc"]
    except Exception:
        return None


async def _fetch_fear_greed() -> int | None:
    r = await _get("https://api.alternative.me/fng/?limit=1&format=json")
    if not r:
        return None
    try:
        return int(r.json()["data"][0]["value"])
    except Exception:
        return None


async def _fetch_funding_rate() -> float | None:
    """Binance BTCUSDT 최신 펀딩레이트 (%)."""
    r = await _get(
        "https://fapi.binance.com/fapi/v1/fundingRate",
        params={"symbol": "BTCUSDT", "limit": "1"},
    )
    if not r:
        return None
    try:
        rate = float(r.json()[0]["fundingRate"])
        return rate * 100  # 소수→퍼센트
    except Exception:
        return None


async def _fetch_mvrv() -> float | None:
    """blockchain.info MVRV 차트에서 최신값."""
    r = await _get(
        "https://api.blockchain.info/charts/mvrv",
        params={"timespan": "5days", "format": "json"},
    )
    if not r:
        return None
    try:
        values = r.json()["values"]
        if values:
            return values[-1]["y"]
    except Exception:
        pass
    return None


async def _fetch_puell() -> float | None:
    """blockchain.info 채굴 수익으로 Puell Multiple 계산.
    Puell = 일일 채굴 수익 / 365일 평균 채굴 수익.
    """
    r = await _get(
        "https://api.blockchain.info/charts/miners-revenue",
        params={"timespan": "2years", "format": "json", "rollingAverage": "1days"},
    )
    if not r:
        return None
    try:
        values = r.json()["values"]
        if len(values) < 365:
            return None
        daily_revenues = [v["y"] for v in values]
        latest = daily_revenues[-1]
        avg_365 = sum(daily_revenues[-365:]) / 365
        if avg_365 > 0:
            return latest / avg_365
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────
# 가격 기반 지표 계산
# ──────────────────────────────────────────────

def _calc_sma(prices: list[float], period: int) -> float | None:
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def _calc_geometric_mean(prices: list[float], period: int) -> float | None:
    if len(prices) < period:
        return None
    subset = prices[-period:]
    try:
        log_sum = sum(math.log(p) for p in subset if p > 0)
        return math.exp(log_sum / len(subset))
    except (ValueError, ZeroDivisionError):
        return None


def _calc_mayer(prices: list[float]) -> float | None:
    """Mayer Multiple = 현재가 / 200DMA."""
    sma200 = _calc_sma(prices, 200)
    if not sma200 or sma200 == 0:
        return None
    return prices[-1] / sma200


def _calc_pi_cycle(prices: list[float]) -> float | None:
    """Pi Cycle Top = 111DMA / (2 × 350DMA). >= 1.0이면 HIT."""
    sma111 = _calc_sma(prices, 111)
    sma350 = _calc_sma(prices, 350)
    if not sma111 or not sma350 or sma350 == 0:
        return None
    return sma111 / (2 * sma350)


def _calc_log_growth(prices: list[float]) -> float | None:
    """Log Growth Curve = price / log_fair_value.
    간소화 모델: BTC genesis부터 일수 기반 log regression.
    fair = 10^(a * log10(days) + b), a≈5.84, b≈-17.01 (Trolololo 근사).
    """
    # BTC genesis: 2009-01-03
    genesis = datetime(2009, 1, 3, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_since_genesis = (now - genesis).days
    if days_since_genesis <= 0:
        return None
    try:
        log_days = math.log10(days_since_genesis)
        # Trolololo log regression coefficients (근사치)
        fair_value = 10 ** (5.84 * log_days - 17.01)
        current_price = prices[-1]
        if fair_value > 0:
            return current_price / fair_value
    except (ValueError, OverflowError):
        pass
    return None


def _calc_ahr999(prices: list[float]) -> float | None:
    """Ahr999 = price / (200d_geometric_mean × log_fitted_price).
    >= 1.2이면 고평가(매도 고려), < 0.45이면 저평가(적립).
    """
    if len(prices) < 200:
        return None
    geo_mean = _calc_geometric_mean(prices, 200)
    if not geo_mean or geo_mean == 0:
        return None

    # Log fitted price (같은 Trolololo 모델 사용)
    genesis = datetime(2009, 1, 3, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_since_genesis = (now - genesis).days
    try:
        log_days = math.log10(days_since_genesis)
        fitted_price = 10 ** (5.84 * log_days - 17.01)
    except (ValueError, OverflowError):
        return None

    current_price = prices[-1]
    denominator = geo_mean * fitted_price
    if denominator == 0:
        return None
    # Ahr999 원래 공식: price / (geo_mean) 와 price / fitted를 조합
    # 간소화: (price / geo_mean) * (price / fitted) 의 기하평균
    ratio_geo = current_price / geo_mean
    ratio_fit = current_price / fitted_price
    return math.sqrt(ratio_geo * ratio_fit)


# ──────────────────────────────────────────────
# NUPL 추정 (MVRV 기반 간이 변환)
# NUPL ≈ 1 - 1/MVRV (근사치, 정확하진 않지만 방향성 일치)
# ──────────────────────────────────────────────

def _estimate_nupl(mvrv: float | None) -> float | None:
    if mvrv is None or mvrv == 0:
        return None
    return 1 - (1 / mvrv)


# ──────────────────────────────────────────────
# 메인 fetch + evaluate
# ──────────────────────────────────────────────

async def fetch_top_signals() -> dict:
    """12개 지표 데이터를 수집하고 HIT/CLEAR 판정."""

    # 병렬 fetch
    prices_task = asyncio.create_task(_fetch_coingecko_history(400))
    dominance_task = asyncio.create_task(_fetch_btc_dominance())
    fg_task = asyncio.create_task(_fetch_fear_greed())
    funding_task = asyncio.create_task(_fetch_funding_rate())
    mvrv_task = asyncio.create_task(_fetch_mvrv())
    puell_task = asyncio.create_task(_fetch_puell())

    prices = await prices_task
    dominance = await dominance_task
    fg = await fg_task
    funding = await funding_task
    mvrv = await mvrv_task
    puell = await puell_task

    # 가격 기반 계산
    mayer = _calc_mayer(prices) if prices else None
    pi_cycle = _calc_pi_cycle(prices) if prices else None
    log_growth = _calc_log_growth(prices) if prices else None
    ahr999 = _calc_ahr999(prices) if prices else None
    nupl = _estimate_nupl(mvrv)

    # 결과 조립
    values = {
        "mvrv": mvrv,
        "nupl": nupl,
        "puell": puell,
        "pi_cycle": pi_cycle,
        "dominance": dominance,
        "mayer": mayer,
        "log_growth": log_growth,
        "fear_greed": fg,
        "funding": funding,
        "exchange_inflow": None,  # 무료 API 소스 없음
        "etf_outflow": None,      # 무료 API 소스 없음
        "ahr999": ahr999,
    }

    return _evaluate(values)


def _is_hit(value: float | None, threshold: float, op: str) -> bool | None:
    if value is None:
        return None
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    return None


def _evaluate(values: dict) -> dict:
    """각 지표의 HIT/CLEAR 상태를 판정."""
    results = []
    hits = 0
    total_online = 0

    for ind in INDICATORS:
        val = values.get(ind["id"])
        hit = _is_hit(val, ind["threshold"], ind["op"])

        if val is not None:
            total_online += 1
            if hit:
                hits += 1

        results.append({
            **ind,
            "value": val,
            "hit": hit,
        })

    # 리스크 레벨 판정
    if total_online == 0:
        risk_level = "UNKNOWN"
        risk_emoji = "❓"
    elif hits == 0:
        risk_level = "SAFE"
        risk_emoji = "🟢"
    elif hits <= 2:
        risk_level = "LOW"
        risk_emoji = "🟡"
    elif hits <= 5:
        risk_level = "MODERATE"
        risk_emoji = "🟠"
    elif hits <= 8:
        risk_level = "HIGH"
        risk_emoji = "🔴"
    else:
        risk_level = "EXTREME"
        risk_emoji = "🚨"

    return {
        "indicators": results,
        "hits": hits,
        "total": len(INDICATORS),
        "online": total_online,
        "risk_level": risk_level,
        "risk_emoji": risk_emoji,
        "timestamp": datetime.now(timezone(timedelta(hours=9))).strftime("%m/%d %H:%M"),
    }


# ──────────────────────────────────────────────
# 포맷터 — 텔레그램 메시지 생성
# ──────────────────────────────────────────────

def format_top_signal(data: dict) -> str:
    """Top Signal 결과를 텔레그램 메시지로 포맷."""
    lines = []
    lines.append(f"🔥 Top Signal ({data['timestamp']})")
    lines.append("")
    lines.append(f"■ 시그널: {data['hits']}/{data['total']}  {data['risk_emoji']}{data['risk_level']}")
    lines.append("")

    # 카테고리별 그룹핑
    categories = ["On-Chain", "Cycle", "Sentiment", "Derivatives", "Flow"]
    for cat in categories:
        cat_indicators = [i for i in data["indicators"] if i["cat"] == cat]
        if not cat_indicators:
            continue

        for ind in cat_indicators:
            val = ind["value"]
            if val is None:
                val_str = "—"
                status = "⬜"
            else:
                # 값 포맷팅
                if ind["id"] == "dominance":
                    val_str = f"{val:.1f}%"
                elif ind["id"] == "funding":
                    val_str = f"{val:.4f}%"
                elif ind["id"] == "etf_outflow":
                    val_str = f"{int(val)}일"
                elif ind["id"] == "exchange_inflow":
                    val_str = f"{val:.2f}×"
                elif ind["id"] == "log_growth":
                    val_str = f"{val:.3f}×"
                elif ind["id"] == "fear_greed":
                    val_str = f"{int(val)}"
                else:
                    val_str = f"{val:.3f}"

                status = "🚨" if ind["hit"] else "✅"

            # threshold 표시
            if ind["op"] == ">=":
                thr_str = f"≥{ind['threshold']}"
            else:
                thr_str = f"≤{ind['threshold']}"

            lines.append(f"{status} {ind['name']:<15} {val_str:<10} ({thr_str})")

    lines.append("")

    # 간단한 해석
    if data["hits"] == 0:
        lines.append("💬 사이클 과열 징후 없음. 안전 구간.")
    elif data["hits"] <= 2:
        lines.append("💬 일부 경고 초기. 주시 필요.")
    elif data["hits"] <= 5:
        lines.append("💬 과열 징후 증가. 리스크 관리 강화.")
    elif data["hits"] <= 8:
        lines.append("💬 다수 지표 과열. 비중 축소 고려.")
    else:
        lines.append("💬 역사적 사이클 탑 수준. 방어 모드.")

    return "\n".join(lines)
