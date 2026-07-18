from __future__ import annotations

from dataclasses import dataclass
import json
import re
from statistics import median
from urllib.parse import quote
from urllib.request import Request, urlopen

from .models import ParsedItem


API_ROOT = "https://www.pathofexile.com/api/trade"
USER_AGENT = "PoENavi/poetore-local-spike (github.com/buri34/poenavi)"


class TradeApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class PriceListing:
    amount: float
    currency: str
    account: str = ""


@dataclass(frozen=True)
class PriceResult:
    league: str
    query_id: str
    total: int
    listings: tuple[PriceListing, ...]
    rate_limit: str = ""

    def median_by_currency(self) -> dict[str, float]:
        grouped: dict[str, list[float]] = {}
        for listing in self.listings:
            grouped.setdefault(listing.currency, []).append(listing.amount)
        return {currency: median(values) for currency, values in grouped.items()}


def _request_json(url: str, payload: dict | None = None) -> tuple[dict, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers)
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8")), response.headers
    except Exception as exc:
        raise TradeApiError(f"PoE Trade APIへの接続に失敗しました: {exc}") from exc


def active_pc_league() -> str:
    data, _ = _request_json(f"{API_ROOT}/data/leagues")
    leagues = [row for row in data.get("result", ()) if row.get("realm") == "pc"]
    for row in leagues:
        name = str(row.get("id", ""))
        lowered = name.lower()
        if name and all(word not in lowered for word in ("hardcore", "ruthless", "standard")):
            return name
    return "Standard"


def physical_dps(item: ParsedItem) -> float | None:
    damage = item.properties.get("物理ダメージ") or item.properties.get("Physical Damage")
    speed = item.properties.get("秒間アタック回数") or item.properties.get("Attacks per Second")
    if not damage or not speed:
        return None
    damage_values = re.findall(r"\d+(?:\.\d+)?", damage)
    speed_values = re.findall(r"\d+(?:\.\d+)?", speed)
    if len(damage_values) < 2 or not speed_values:
        return None
    return ((float(damage_values[0]) + float(damage_values[1])) / 2) * float(speed_values[0])


def build_search_query(item: ParsedItem, trade_base_type: str | None = None) -> dict:
    base_type = (trade_base_type or item.base_type).strip()
    query: dict = {
        "status": {"option": "online"},
        "type": base_type,
        "stats": [{"type": "and", "filters": []}],
        "filters": {"trade_filters": {"filters": {"price": {"option": "chaos"}}}},
    }
    rarity = item.rarity.lower()
    rarity_option = {"レア": "rare", "rare": "rare", "ユニーク": "unique", "unique": "unique"}.get(rarity)
    if rarity_option:
        query["filters"]["type_filters"] = {"filters": {"rarity": {"option": rarity_option}}}
    pdps = physical_dps(item)
    if item.category == "weapon" and pdps is not None:
        query["filters"]["weapon_filters"] = {"filters": {"pdps": {"min": round(pdps * 0.8, 1)}}}
    return {"query": query, "sort": {"price": "asc"}}


def search_prices(item: ParsedItem, trade_base_type: str | None = None, league: str | None = None) -> PriceResult:
    league = league or active_pc_league()
    search, headers = _request_json(
        f"{API_ROOT}/search/{quote(league, safe='')}", build_search_query(item, trade_base_type)
    )
    query_id = str(search.get("id", ""))
    ids = list(search.get("result", ()))
    if not query_id:
        raise TradeApiError("検索IDを取得できませんでした。")
    listings: list[PriceListing] = []
    if ids:
        fetch_ids = ",".join(ids[:10])
        fetched, _ = _request_json(f"{API_ROOT}/fetch/{fetch_ids}?query={quote(query_id)}")
        for row in fetched.get("result", ()):
            listing = row.get("listing", {})
            price = listing.get("price") or {}
            if price.get("amount") is None or not price.get("currency"):
                continue
            account = (listing.get("account") or {}).get("name", "")
            listings.append(PriceListing(float(price["amount"]), str(price["currency"]), str(account)))
    rate_limit = headers.get("X-Rate-Limit-Ip-State", "") if headers else ""
    return PriceResult(league, query_id, len(ids), tuple(listings), rate_limit)
