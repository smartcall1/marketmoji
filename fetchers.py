import re
import httpx
from bs4 import BeautifulSoup
from config import USER_AGENT, REQUEST_TIMEOUT

HEADERS = {"User-Agent": USER_AGENT}


async def _get(url: str, headers: dict | None = None, retries: int = 2) -> httpx.Response | None:
    """기본 헤더는 브라우저 UA. FRED는 봇 UA를 차단하므로 호출 시 headers={}로 우회.
    FRED는 간헐적으로 ReadTimeout/ReadError 던지므로 retries로 재시도."""
    if headers is None:
        headers = HEADERS
    last_exc = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=headers, follow_redirects=True) as c:
                r = await c.get(url)
                r.raise_for_status()
                return r
        except Exception as e:
            last_exc = e
            continue
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
        "?id=BAMLH0A0HYM2&cosd=2020-01-01",
        headers={},
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


async def _fred_csv_latest(series_id: str, cosd: str = "2020-01-01") -> tuple[str, float] | None:
    """FRED CSV의 최신 유효 데이터 1개를 (date, value)로 반환. FRED는 봇 UA 차단 → 헤더 비움."""
    r = await _get(
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={cosd}",
        headers={},
    )
    if not r:
        return None
    try:
        lines = r.text.strip().split("\n")
        for line in reversed(lines):
            parts = line.split(",")
            if len(parts) == 2 and parts[1] not in (".", "") and parts[0] != "observation_date":
                return parts[0], float(parts[1])
    except Exception:
        pass
    return None


async def fetch_core_cpi_yoy() -> tuple[str, float] | None:
    """Core CPI YoY %. FRED CPILFESL 인덱스 → 12개월 전 대비 %변화."""
    r = await _get(
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPILFESL&cosd=2022-01-01",
        headers={},
    )
    if not r:
        return None
    try:
        rows: list[tuple[str, float]] = []
        for line in r.text.strip().split("\n"):
            parts = line.split(",")
            if len(parts) == 2 and parts[1] not in (".", "") and parts[0] != "observation_date":
                rows.append((parts[0], float(parts[1])))
        if len(rows) < 13:
            return None
        latest_date, latest = rows[-1]
        _, year_ago = rows[-13]
        if year_ago <= 0:
            return None
        yoy = (latest / year_ago - 1) * 100
        return latest_date, round(yoy, 2)
    except Exception:
        return None


async def fetch_sticky_core_cpi() -> tuple[str, float] | None:
    """Sticky Price CPI less Food & Energy, 12-month % change. FRED CORESTICKM159SFRBATL."""
    return await _fred_csv_latest("CORESTICKM159SFRBATL", "2022-01-01")


async def fetch_sticky_cpi_ex_shelter() -> tuple[str, float] | None:
    """Sticky Price CPI ex Shelter, 12-month % change. FRED STICKCPIXSHLTRM159SFRBATL.
    블로그 본문의 '주거비 제외 core sticky CPI 3.4%' 대용 (food/energy 포함이라 정확한 core는 아니나 가장 근접)."""
    return await _fred_csv_latest("STICKCPIXSHLTRM159SFRBATL", "2022-01-01")


async def _fred_csv_history(series_id: str, cosd: str) -> list[tuple[str, float]] | None:
    """FRED CSV의 (date, value) 시퀀스 전체. 추세 판정용."""
    r = await _get(
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={cosd}",
        headers={},
    )
    if not r:
        return None
    try:
        rows: list[tuple[str, float]] = []
        for line in r.text.strip().split("\n"):
            parts = line.split(",")
            if len(parts) == 2 and parts[1] not in (".", "") and parts[0] != "observation_date":
                rows.append((parts[0], float(parts[1])))
        return rows if rows else None
    except Exception:
        return None


async def fetch_10y_history(days: int = 30) -> list[float] | None:
    """Yahoo ^TNX 일간 10Y Treasury Yield 시퀀스 (oldest→newest, None 제거)."""
    r = await _get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?range=3mo&interval=1d"
    )
    if not r:
        return None
    try:
        d = r.json()
        closes = d["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        clean = [float(c) for c in closes if c is not None]
        return clean[-days:] if days else clean
    except Exception:
        return None


async def fetch_core_cpi_yoy_history(months: int = 6) -> list[tuple[str, float]] | None:
    """Core CPI YoY % 시퀀스. CPILFESL 인덱스에서 12개월 슬라이딩 YoY 계산."""
    rows = await _fred_csv_history("CPILFESL", "2021-01-01")
    if not rows or len(rows) < 13:
        return None
    yoys: list[tuple[str, float]] = []
    for i in range(12, len(rows)):
        date_i, val_i = rows[i]
        _, val_prev = rows[i - 12]
        if val_prev > 0:
            yoys.append((date_i, round((val_i / val_prev - 1) * 100, 2)))
    return yoys[-months:] if months else yoys


async def fetch_sticky_ex_shelter_history(months: int = 6) -> list[tuple[str, float]] | None:
    """Sticky CPI ex-Shelter 12-month % change 시퀀스."""
    rows = await _fred_csv_history("STICKCPIXSHLTRM159SFRBATL", "2024-01-01")
    if not rows:
        return None
    return rows[-months:] if months else rows


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
