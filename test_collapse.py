"""붕괴 시그널 로컬 검증 스크립트."""
import asyncio
import httpx
import sys

sys.path.insert(0, r'D:\Codes\market_dashboard_bot')
from config import USER_AGENT, REQUEST_TIMEOUT
from collapse_signal import fetch_collapse_signals, format_collapse_signal


async def probe(url: str, with_hdr: bool):
    hdr = {"User-Agent": USER_AGENT} if with_hdr else {}
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT, headers=hdr, follow_redirects=True
        ) as c:
            r = await c.get(url)
            return r.status_code, len(r.text), r.text[:120]
    except Exception as e:
        return None, None, repr(e)


async def main():
    print("=" * 60)
    print("1) FRED 헤더 유무별 응답 비교")
    print("=" * 60)
    urls = [
        ("CPILFESL hdr",   "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPILFESL&cosd=2022-01-01", True),
        ("CPILFESL nohdr", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPILFESL&cosd=2022-01-01", False),
        ("BAMLH0A0HYM2 hdr", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2&cosd=2020-01-01", True),
        ("CORESTICKM159SFRBATL hdr", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CORESTICKM159SFRBATL&cosd=2022-01-01", True),
        ("STICKCPIXSHLTRM159SFRBATL hdr", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=STICKCPIXSHLTRM159SFRBATL&cosd=2022-01-01", True),
    ]
    for name, url, h in urls:
        s, l, p = await probe(url, h)
        print(f"{name}: status={s} len={l}")
        print(f"  preview: {p[:100]}")

    print()
    print("=" * 60)
    print("2) fetch_collapse_signals() 풀 호출")
    print("=" * 60)
    data = await fetch_collapse_signals()
    print(format_collapse_signal(data))
    print()
    print("--- RAW ---")
    for s in data["signals"]:
        print(f"  {s['id']:<20} value={s['value']} state={s['state']} date={s.get('date')}")


if __name__ == "__main__":
    asyncio.run(main())
