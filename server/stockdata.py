"""StockData pool — legacy T01 collector proxy.
Base: STOCKDATA_URL (default stockdata:15437).
Sectors v2 (server/sectors.py) is the single market-data gateway; keyless ->
honest sectors_missing_key, never a silent third-party fallback.
"""
import httpx
import logging
from typing import Optional

log = logging.getLogger(__name__)


class StockDataClient:
    def __init__(self, base_url: str, timeout: int = 8):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def startup(self):
        self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
        log.info(f"stockdata pool ready -> {self.base_url}")

    async def shutdown(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, params: dict | None = None) -> Optional[dict]:
        if not self._client:
            return None
        url = f"{self.base_url}{path}"
        try:
            r = await self._client.get(url, params=params)
            if r.status_code == 200:
                return r.json()
            log.warning(f"stockdata {r.status_code} {url}")
            return None
        except Exception as e:
            log.warning(f"stockdata unreachable {url}: {e}")
            return None

    async def get_overview(self, ticker: str) -> Optional[dict]:
        for p in [
            f"/overview/{ticker}",
            f"/company/{ticker}/overview",
            f"/company/report/{ticker}?sections=overview",
        ]:
            data = await self._get(p)
            if data:
                return data
        return None

    async def get_financials(self, ticker: str, years: int = 5) -> Optional[dict]:
        for p in [
            f"/financials/{ticker}?years={years}",
            f"/company/{ticker}/financials",
            f"/company/quarterly-financials/{ticker}",
        ]:
            data = await self._get(p)
            if data:
                return data
        return None

    async def get_segments(self, ticker: str, year: int = 2024) -> Optional[dict]:
        for p in [f"/segments/{ticker}/{year}", f"/company/segments/{ticker}/{year}"]:
            data = await self._get(p)
            if data:
                return data
        return None

    async def get_prices(self, ticker: str, period: str = "5y") -> Optional[dict]:
        for p in [f"/prices/{ticker}?period={period}", f"/transaction/daily/{ticker}?period={period}"]:
            data = await self._get(p)
            if data:
                return data
        return None

    async def health(self) -> dict:
        if not self._client:
            return {"ok": False, "reason": "not started"}
        try:
            r = await self._client.get(f"{self.base_url}/health", timeout=3)
            if r.status_code == 200:
                return {"ok": True, "data": r.json()}
            r2 = await self._client.get(self.base_url, timeout=3)
            return {"ok": r2.status_code < 500, "status": r2.status_code}
        except Exception as e:
            return {"ok": False, "reason": str(e)}


_stock: Optional[StockDataClient] = None


def get_stockdata() -> StockDataClient:
    global _stock
    if _stock is None:
        from .config import get_settings

        s = get_settings()
        _stock = StockDataClient(s.stockdata_url, s.stockdata_timeout)
    return _stock
