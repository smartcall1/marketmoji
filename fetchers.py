import re
import httpx
from bs4 import BeautifulSoup
from config import USER_AGENT, REQUEST_TIMEOUT

HEADERS = {"User-Agent": USER_AGENT}


async def _get(url: str) -> httpx.Response | None:
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=HEADERS, follow_redirects=True) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r
    except Exception:
        return None


def _parse_multpl(html: str) -> float | None:
    soup = BeautifulSoup(html, "html.parser")
    el = soup.select_one("#current")
    if not el:
        return None
    text = el.get_text(" ", strip=True).replace(",", "").replace("%", "")
    m = re.search(r"(\d+\.\d+)", text)
    if m:
        return float(m.group(1))
    return None


async def fetch_cape() -> float | None:
    r = await _get("https://www.multpl.com/shiller-pe")
    return _parse_multpl(r.text) if r else None


async def fetch_real_rate() -> float | None:
    r = await _get("https://www.multpl.com/10-year-real-interest-rate")
    return _parse_multpl(r.text) if r else None


async def fetch_10y_rate() -> float | None:
    r = await _get("https://www.multpl.com/10-year-treasury-rate")
    return _parse_multpl(r.text) if r else None


async def fetch_2y_rate() -> float | None:
    r = await _get("https://www.multpl.com/2-year-treasury-rate")
    return _parse_multpl(r.text) if r else None


async def fetch_buffett() -> float | None:
    r = await _get("https://currentmarketvaluation.com/models/buffett-indicator.php")
    if not r:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup.find_all(string=re.compile(r"\d{2,3}(\.\d+)?%")):
        parent = tag.find_parent()
        if parent and ("ratio" in (parent.get_text() or "").lower() or "indicator" in (parent.get_text() or "").lower()):
            m = re.search(r"(\d{2,4}(?:\.\d+)?)%", tag)
            if m:
                return float(m.group(1))
    text = r.text
    m = re.search(r"Buffett Indicator[^<]*?(\d{2,4}(?:\.\d+)?)%", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"ratio[^<]*?(\d{2,4}(?:\.\d+)?)%", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


async def fetch_vix() -> float | None:
    r = await _get("https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=1d&interval=1d")
    if not r:
        return None
    try:
        data = r.json()
        return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception:
        return None


async def fetch_cnn_fg() -> tuple[int, str] | None:
    r = await _get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata")
    if not r:
        return None
    try:
        data = r.json()
        score = int(round(data["fear_and_greed"]["score"]))
        rating = data["fear_and_greed"]["rating"]
        return score, rating
    except Exception:
        return None


async def fetch_crypto_fg() -> tuple[int, str] | None:
    r = await _get("https://api.alternative.me/fng/?limit=1&format=json")
    if not r:
        return None
    try:
        data = r.json()
        entry = data["data"][0]
        return int(entry["value"]), entry["value_classification"]
    except Exception:
        return None


async def fetch_credit_spread() -> float | None:
    r = await _get(
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        "?id=BAMLH0A0HYM2&cosd=2020-01-01"
    )
    if not r:
        return None
    try:
        lines = r.text.strip().split("\n")
        for line in reversed(lines):
            parts = line.split(",")
            if len(parts) == 2 and parts[1] not in (".", ""):
                return float(parts[1])
    except Exception:
        pass
    return None


AI_BIG_10 = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "MU", "AMD"]


def _parse_mcap(text: str) -> float | None:
    text = text.strip().replace(",", "")
    m = re.match(r"([\d.]+)\s*([TBM])", text)
    if not m:
        return None
    val = float(m.group(1))
    suffix = m.group(2)
    return val * {"T": 1e12, "B": 1e9, "M": 1e6}[suffix]


async def fetch_concentration() -> float | None:
    """S&P 500 내 AI Big 10 시가총액 집중도(%)."""
    r = await _get("https://stockanalysis.com/list/sp-500-stocks/")
    if not r:
        return None
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            return None

        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        sym_idx = headers.index("Symbol")
        name_idx = headers.index("Company Name")
        mcap_idx = headers.index("Market Cap")

        seen_companies: set[str] = set()
        total_mcap = 0.0
        big10_mcap = 0.0

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) <= mcap_idx:
                continue
            symbol = cols[sym_idx].get_text(strip=True)
            name = cols[name_idx].get_text(strip=True)
            mcap = _parse_mcap(cols[mcap_idx].get_text(strip=True))
            if mcap is None or name in seen_companies:
                continue
            seen_companies.add(name)
            total_mcap += mcap
            if symbol in AI_BIG_10:
                big10_mcap += mcap

        if total_mcap <= 0:
            return None
        return round(big10_mcap / total_mcap * 100, 1)
    except Exception:
        return None


async def fetch_all() -> dict:
    import asyncio

    cape_t = asyncio.create_task(fetch_cape())
    real_rate_t = asyncio.create_task(fetch_real_rate())
    rate_10y_t = asyncio.create_task(fetch_10y_rate())
    rate_2y_t = asyncio.create_task(fetch_2y_rate())
    buffett_t = asyncio.create_task(fetch_buffett())
    vix_t = asyncio.create_task(fetch_vix())
    cnn_fg_t = asyncio.create_task(fetch_cnn_fg())
    crypto_fg_t = asyncio.create_task(fetch_crypto_fg())
    credit_t = asyncio.create_task(fetch_credit_spread())
    conc_t = asyncio.create_task(fetch_concentration())

    cape = await cape_t
    real_rate = await real_rate_t
    rate_10y = await rate_10y_t
    rate_2y = await rate_2y_t
    buffett = await buffett_t
    vix = await vix_t
    cnn_fg = await cnn_fg_t
    crypto_fg = await crypto_fg_t
    credit_spread = await credit_t
    concentration = await conc_t

    ecy = None
    if cape and real_rate and cape > 0:
        ecy = (1 / cape) * 100 - real_rate

    yield_curve = None
    if rate_10y is not None and rate_2y is not None:
        yield_curve = rate_10y - rate_2y

    return {
        "cape": cape,
        "ecy": ecy,
        "real_rate": real_rate,
        "rate_10y": rate_10y,
        "rate_2y": rate_2y,
        "buffett": buffett,
        "yield_curve": yield_curve,
        "vix": vix,
        "cnn_fg": cnn_fg,
        "crypto_fg": crypto_fg,
        "credit_spread": credit_spread,
        "concentration": concentration,
    }
