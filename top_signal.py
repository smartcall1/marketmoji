"""
Top Signal — BTC 사이클 꼭대기 감지 12개 지표 종합.
무료 공개 API만 사용, Termux/ARM 호환 (브라우저 불필요).

데이터 소스:
  - AskSurf API (MVRV, NUPL, Puell, Exchange Inflow) — 30크레딧/일 무료
  - CoinGecko (가격 히스토리 → Pi Cycle, Mayer, Log Growth, Ahr999, Dominance)
  - Binance (Perp Funding Rate)
  - alternative.me (Fear & Greed)
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

SURF_API = "https://api.asksurf.ai/gateway/v1/market/onchain-indicator"

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
# AskSurf API fetcher (MVRV, NUPL, Puell, Exchange Inflow)
# 30크레딧/일 무료. 하루 1회 실행 시 4크레딧 소모.
# ──────────────────────────────────────────────

async def _fetch_surf_metric(metric: str) -> float | None:
    """AskSurf API에서 BTC on-chain 지표 최신값 조회."""
    r = await _get(SURF_API, params={"symbol": "BTC", "metric": metric})
    if not r:
        return None
    try:
        data = r.json()
        if isinstance(data, list) and data:
            return float(data[-1]["value"])
        if isinstance(data, dict) and "data" in data:
            entries = data["data"]
            if isinstance(entries, list) and entries:
                return float(entries[-1]["value"])
    except Exception:
        pass
    return None


async def _fetch_surf_exchange_inflow() -> float | None:
    """Exchange inflow ratio (today / 30d avg). Surf metric: exchange-flows/inflows."""
    r = await _get(SURF_API, params={"symbol": "BTC", "metric": "exchange-flows/inflows"})
    if not r:
        return None
    try:
        data = r.json()
        entries = data if isinstance(data, list) else data.get("data", [])
        if not entries or len(entries) < 30:
            return None
        values = [float(e["value"]) for e in entries]
        latest = values[-1]
        avg_30d = sum(values[-30:]) / 30
        if avg_30d > 0:
            return latest / avg_30d
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────
# CoinGecko fetcher (가격 히스토리, 도미넌스)
# ──────────────────────────────────────────────

async def _fetch_coingecko_history() -> list[float] | None:
    """CoinGecko BTC 일별 종가 365일 (oldest→newest)."""
    r = await _get(
        "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
        params={"vs_currency": "usd", "days": "365", "interval": "daily"},
    )
    if not r:
        return None
    try:
        prices = r.json()["prices"]
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


# ──────────────────────────────────────────────
# 기타 무료 API
# ──────────────────────────────────────────────

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
        return rate * 100
    except Exception:
        return None


# ──────────────────────────────────────────────
# Fallback: blockchain.info (Puell 백업)
# ──────────────────────────────────────────────

async def _fetch_puell_fallback() -> float | None:
    """blockchain.info 채굴 수익으로 Puell Multiple 계산."""
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
    sma200 = _calc_sma(prices, 200)
    if not sma200 or sma200 == 0:
        return None
    return prices[-1] / sma200


def _calc_pi_cycle(prices: list[float]) -> float | None:
    """111DMA / (2 × 350DMA). 350일 데이터 부족 시 가용 데이터로 계산."""
    sma111 = _calc_sma(prices, 111)
    if not sma111:
        return None
    sma350 = _calc_sma(prices, 350)
    if not sma350:
        sma350 = _calc_sma(prices, len(prices))
    if not sma350 or sma350 == 0:
        return None
    return sma111 / (2 * sma350)


def _calc_log_growth(prices: list[float]) -> float | None:
    """price / log_fair_value (Trolololo log regression)."""
    genesis = datetime(2009, 1, 3, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_since_genesis = (now - genesis).days
    if days_since_genesis <= 0:
        return None
    try:
        log_days = math.log10(days_since_genesis)
        fair_value = 10 ** (5.84 * log_days - 17.01)
        current_price = prices[-1]
        if fair_value > 0:
            return current_price / fair_value
    except (ValueError, OverflowError):
        pass
    return None


def _calc_ahr999(prices: list[float]) -> float | None:
    """sqrt((price/geo_mean_200d) * (price/fitted_price))."""
    if len(prices) < 200:
        return None
    geo_mean = _calc_geometric_mean(prices, 200)
    if not geo_mean or geo_mean == 0:
        return None

    genesis = datetime(2009, 1, 3, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_since_genesis = (now - genesis).days
    try:
        log_days = math.log10(days_since_genesis)
        fitted_price = 10 ** (5.84 * log_days - 17.01)
    except (ValueError, OverflowError):
        return None

    current_price = prices[-1]
    if fitted_price <= 0:
        return None
    ratio_geo = current_price / geo_mean
    ratio_fit = current_price / fitted_price
    return math.sqrt(ratio_geo * ratio_fit)


# ──────────────────────────────────────────────
# 메인 fetch + evaluate
# ──────────────────────────────────────────────

async def fetch_top_signals() -> dict:
    """12개 지표 데이터를 수집하고 HIT/CLEAR 판정."""

    # 병렬 fetch — Surf API (4크레딧) + CoinGecko + 기타
    mvrv_task = asyncio.create_task(_fetch_surf_metric("mvrv"))
    nupl_task = asyncio.create_task(_fetch_surf_metric("nupl"))
    puell_task = asyncio.create_task(_fetch_surf_metric("puell-multiple"))
    inflow_task = asyncio.create_task(_fetch_surf_exchange_inflow())
    prices_task = asyncio.create_task(_fetch_coingecko_history())
    dominance_task = asyncio.create_task(_fetch_btc_dominance())
    fg_task = asyncio.create_task(_fetch_fear_greed())
    funding_task = asyncio.create_task(_fetch_funding_rate())
    puell_fb_task = asyncio.create_task(_fetch_puell_fallback())

    mvrv = await mvrv_task
    nupl = await nupl_task
    puell = await puell_task
    exchange_inflow = await inflow_task
    prices = await prices_task
    dominance = await dominance_task
    fg = await fg_task
    funding = await funding_task
    puell_fb = await puell_fb_task

    # Surf 실패 시 fallback
    if puell is None:
        puell = puell_fb

    # 가격 기반 계산
    mayer = _calc_mayer(prices) if prices else None
    pi_cycle = _calc_pi_cycle(prices) if prices else None
    log_growth = _calc_log_growth(prices) if prices else None
    ahr999 = _calc_ahr999(prices) if prices else None

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
        "exchange_inflow": exchange_inflow,
        "etf_outflow": None,  # 무료 API 소스 없음 (ETF 데이터는 유료)
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
    lines = []
    lines.append(f"🔥 Top Signal — BTC 사이클 꼭대기 감지 ({data['timestamp']})")
    lines.append("")
    lines.append(f"■ 시그널: {data['hits']}/{data['total']}  {data['risk_emoji']}{data['risk_level']}")
    lines.append("")

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

            if ind["op"] == ">=":
                thr_str = f"≥{ind['threshold']}"
            else:
                thr_str = f"≤{ind['threshold']}"

            lines.append(f"{status} {ind['name']:<15} {val_str:<10} ({thr_str})")

    lines.append("")

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
