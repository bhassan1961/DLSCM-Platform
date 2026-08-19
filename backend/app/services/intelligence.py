"""
Crisis Intelligence Aggregator

Fetches real-time intelligence from multiple humanitarian data sources:
- ReliefWeb API (UN OCHA) — situation reports, news, analyses
- GDACS (Global Disaster Alert and Coordination System) — disaster alerts
- RSS news feeds — major humanitarian news outlets
"""

import asyncio
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import httpx

RELIEFWEB_API = "https://api.reliefweb.int/v1"

GDACS_RSS = "https://www.gdacs.org/xml/rss.xml"

NEWS_FEEDS = [
    {
        "name": "ReliefWeb Updates",
        "url": "https://reliefweb.int/updates/rss.xml",
        "source_type": "humanitarian",
    },
    {
        "name": "UNOCHA",
        "url": "https://www.unocha.org/rss",
        "source_type": "humanitarian",
    },
    {
        "name": "ICRC News",
        "url": "https://www.icrc.org/en/rss/news",
        "source_type": "humanitarian",
    },
]

ALL_NEWS_FEEDS = [
    {
        "id": "reliefweb",
        "name": "ReliefWeb",
        "url": "https://reliefweb.int/updates/rss.xml",
        "category": "humanitarian",
    },
    {
        "id": "unocha",
        "name": "UN OCHA",
        "url": "https://www.unocha.org/rss",
        "category": "humanitarian",
    },
    {
        "id": "icrc",
        "name": "ICRC",
        "url": "https://www.icrc.org/en/rss/news",
        "category": "humanitarian",
    },
    {
        "id": "who",
        "name": "WHO News",
        "url": "https://www.who.int/rss-feeds/news-english.xml",
        "category": "health",
    },
    {
        "id": "gdacs",
        "name": "GDACS",
        "url": "https://www.gdacs.org/xml/rss.xml",
        "category": "alerts",
    },
    {
        "id": "aljazeera",
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "news",
    },
    {
        "id": "bbc",
        "name": "BBC World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "news",
    },
    {
        "id": "reuters",
        "name": "Reuters",
        "url": "https://www.reutersagency.com/feed/",
        "category": "news",
    },
    {
        "id": "guardian",
        "name": "The Guardian",
        "url": "https://www.theguardian.com/world/rss",
        "category": "news",
    },
    {
        "id": "ap",
        "name": "AP News",
        "url": "https://rsshub.app/apnews/topics/apf-topnews",
        "category": "news",
    },
]

DISASTER_TYPE_MAP = {
    "drought": ["drought", "food crisis", "famine", "water shortage", "crop failure"],
    "flood": [
        "flood",
        "flooding",
        "flash flood",
        "river overflow",
        "deluge",
        "inundation",
    ],
    "earthquake": ["earthquake", "seismic", "tremor", "quake", "aftershock"],
    "cyclone": ["cyclone", "hurricane", "typhoon", "tropical storm", "storm surge"],
    "conflict": [
        "conflict",
        "armed",
        "military",
        "war",
        "displacement",
        "refugee",
        "IDP",
    ],
    "epidemic": [
        "epidemic",
        "outbreak",
        "cholera",
        "ebola",
        "covid",
        "disease",
        "pandemic",
    ],
}


def _relevance_score(
    text: str, disaster_name: str, country: str, disaster_type: str
) -> float:
    text_lower = text.lower()
    score = 0.0

    name_parts = disaster_name.lower().split()
    for part in name_parts:
        if len(part) > 2 and part in text_lower:
            score += 0.3

    if country.lower() in text_lower:
        score += 0.25

    type_keywords = DISASTER_TYPE_MAP.get(disaster_type, [])
    for kw in type_keywords:
        if kw in text_lower:
            score += 0.15
            break

    return min(score, 1.0)


def _make_id(source: str, title: str) -> str:
    return hashlib.md5(f"{source}:{title}".encode()).hexdigest()[:12]


async def fetch_reliefweb_reports(
    country: str,
    disaster_type: str,
    disaster_name: str,
    limit: int = 20,
    days_back: int = 90,
) -> list[dict]:
    """Fetch situation reports and updates from ReliefWeb API."""
    since = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
        "%Y-%m-%dT00:00:00+00:00"
    )

    query_parts = []
    if country:
        query_parts.append(country)
    type_keywords = DISASTER_TYPE_MAP.get(disaster_type, [])
    if type_keywords:
        query_parts.append(type_keywords[0])

    params = {
        "appname": "dlscm-platform",
        "query[value]": " ".join(query_parts),
        "filter[field]": "date.created",
        "filter[value][from]": since,
        "sort[]": "date.created:desc",
        "limit": limit,
        "fields[include][]": [
            "title",
            "body-html",
            "url_alias",
            "source",
            "date",
            "country",
            "disaster_type",
            "format",
            "theme",
        ],
    }

    items = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{RELIEFWEB_API}/reports", params=params)
            if resp.status_code == 200:
                data = resp.json()
                for entry in data.get("data", []):
                    fields = entry.get("fields", {})
                    title = fields.get("title", "")
                    body_html = fields.get("body-html", "")
                    body_text = (
                        re.sub(r"<[^>]+>", "", body_html)[:500] if body_html else ""
                    )

                    sources = fields.get("source", [])
                    source_name = (
                        sources[0].get("name", "ReliefWeb") if sources else "ReliefWeb"
                    )

                    date_info = fields.get("date", {})
                    pub_date = date_info.get("created", "")

                    countries = fields.get("country", [])
                    country_names = [c.get("name", "") for c in countries]

                    disaster_types = fields.get("disaster_type", [])
                    dtype_names = [dt.get("name", "") for dt in disaster_types]

                    formats = fields.get("format", [])
                    format_name = (
                        formats[0].get("name", "Report") if formats else "Report"
                    )

                    full_text = f"{title} {body_text}"
                    score = _relevance_score(
                        full_text, disaster_name, country, disaster_type
                    )

                    if score < 0.15:
                        continue

                    items.append(
                        {
                            "id": _make_id("reliefweb", title),
                            "source": "ReliefWeb",
                            "source_org": source_name,
                            "source_type": "situation_report",
                            "category": _categorize_format(format_name),
                            "title": title,
                            "summary": body_text[:300] + "..."
                            if len(body_text) > 300
                            else body_text,
                            "url": f"https://reliefweb.int{fields.get('url_alias', '')}",
                            "published_at": pub_date,
                            "countries": country_names,
                            "disaster_types": dtype_names,
                            "relevance_score": round(score, 2),
                        }
                    )
    except (httpx.HTTPError, ET.ParseError, KeyError, ValueError) as e:
        items.append(
            {
                "id": _make_id("reliefweb", "error"),
                "source": "ReliefWeb",
                "source_org": "System",
                "source_type": "error",
                "category": "system",
                "title": f"ReliefWeb fetch failed: {str(e)[:100]}",
                "summary": "Unable to reach ReliefWeb API. Will retry on next request.",
                "url": "",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "countries": [],
                "disaster_types": [],
                "relevance_score": 0,
            }
        )

    return items


def _categorize_format(format_name: str) -> str:
    f = format_name.lower()
    if "situation report" in f or "sitrep" in f:
        return "sitrep"
    if "analysis" in f:
        return "analysis"
    if "assessment" in f:
        return "assessment"
    if "news" in f or "press" in f:
        return "news"
    if "map" in f or "infographic" in f:
        return "map"
    if "appeal" in f or "funding" in f:
        return "funding"
    return "report"


async def fetch_gdacs_alerts(
    country: str,
    disaster_type: str,
    disaster_name: str,
) -> list[dict]:
    """Fetch alerts from GDACS RSS feed filtered by relevance."""
    items = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(GDACS_RSS)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                ns = {"gdacs": "http://www.gdacs.org"}

                for item in root.findall(".//item"):
                    title = item.findtext("title", "")
                    desc = item.findtext("description", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")

                    alert_level = item.findtext("gdacs:alertlevel", "", ns)
                    event_type = item.findtext("gdacs:eventtype", "", ns)
                    gcountry = item.findtext("gdacs:country", "", ns)
                    severity_text = item.findtext("gdacs:severity", "", ns)
                    population = item.findtext("gdacs:population", "", ns)

                    full_text = f"{title} {desc} {gcountry}"
                    score = _relevance_score(
                        full_text, disaster_name, country, disaster_type
                    )

                    if score < 0.15:
                        continue

                    items.append(
                        {
                            "id": _make_id("gdacs", title),
                            "source": "GDACS",
                            "source_org": "GDACS / JRC",
                            "source_type": "alert",
                            "category": "alert",
                            "title": title,
                            "summary": _clean_html(desc)[:300],
                            "url": link,
                            "published_at": _parse_rss_date(pub_date),
                            "countries": [gcountry] if gcountry else [],
                            "disaster_types": [event_type] if event_type else [],
                            "relevance_score": round(score, 2),
                            "alert_level": alert_level,
                            "severity": severity_text,
                            "affected_population": population,
                        }
                    )
    except (httpx.HTTPError, ET.ParseError, KeyError, ValueError):
        pass

    return items


async def fetch_news_feeds(
    country: str,
    disaster_type: str,
    disaster_name: str,
    max_per_feed: int = 10,
) -> list[dict]:
    """Fetch and filter news from RSS feeds."""
    items = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for feed_info in NEWS_FEEDS:
            try:
                resp = await client.get(feed_info["url"])
                if resp.status_code != 200:
                    continue

                root = ET.fromstring(resp.text)
                count = 0

                for item in root.findall(".//item"):
                    if count >= max_per_feed:
                        break

                    title = item.findtext("title", "")
                    desc = item.findtext("description", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")

                    full_text = f"{title} {desc}"
                    score = _relevance_score(
                        full_text, disaster_name, country, disaster_type
                    )

                    if score < 0.2:
                        continue

                    items.append(
                        {
                            "id": _make_id(feed_info["name"], title),
                            "source": feed_info["name"],
                            "source_org": feed_info["name"],
                            "source_type": feed_info["source_type"],
                            "category": "news",
                            "title": title,
                            "summary": _clean_html(desc)[:300],
                            "url": link,
                            "published_at": _parse_rss_date(pub_date),
                            "countries": [],
                            "disaster_types": [],
                            "relevance_score": round(score, 2),
                        }
                    )
                    count += 1
            except (httpx.HTTPError, ET.ParseError, KeyError, ValueError):
                continue

    return items


async def fetch_live_news(
    feed_ids: list[str] | None = None, max_per_feed: int = 20
) -> dict:
    """Fetch latest news from all or selected RSS feeds without relevance filtering."""
    feeds_to_fetch = ALL_NEWS_FEEDS
    if feed_ids:
        feeds_to_fetch = [f for f in ALL_NEWS_FEEDS if f["id"] in feed_ids]

    all_items = []
    feed_meta = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for feed_info in feeds_to_fetch:
            items = []
            try:
                resp = await client.get(feed_info["url"])
                if resp.status_code != 200:
                    feed_meta.append({**feed_info, "status": "error", "count": 0})
                    continue

                root = ET.fromstring(resp.text)
                count = 0

                for item in root.findall(".//item"):
                    if count >= max_per_feed:
                        break

                    title = item.findtext("title", "")
                    desc = item.findtext("description", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")

                    if not title or not title.strip():
                        continue

                    items.append(
                        {
                            "id": _make_id(feed_info["id"], title),
                            "feed_id": feed_info["id"],
                            "feed_name": feed_info["name"],
                            "category": feed_info["category"],
                            "title": title.strip(),
                            "summary": _clean_html(desc)[:200],
                            "url": link,
                            "published_at": _parse_rss_date(pub_date),
                        }
                    )
                    count += 1

                feed_meta.append({**feed_info, "status": "ok", "count": len(items)})
                all_items.extend(items)
            except (httpx.HTTPError, ET.ParseError, KeyError, ValueError):
                feed_meta.append({**feed_info, "status": "error", "count": 0})

    all_items.sort(key=lambda x: x.get("published_at", ""), reverse=True)

    return {
        "items": all_items,
        "total": len(all_items),
        "feeds": feed_meta,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_gdacs_live_alerts() -> list[dict]:
    """Fetch ALL active GDACS alerts with coordinates for map display."""
    items = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(GDACS_RSS)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                ns = {
                    "gdacs": "http://www.gdacs.org",
                    "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
                }

                for item in root.findall(".//item"):
                    title = item.findtext("title", "")
                    desc = item.findtext("description", "")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")

                    alert_level = item.findtext("gdacs:alertlevel", "", ns)
                    event_type = item.findtext("gdacs:eventtype", "", ns)
                    gcountry = item.findtext("gdacs:country", "", ns)
                    severity_text = item.findtext("gdacs:severity", "", ns)
                    population = item.findtext("gdacs:population", "", ns)

                    lat_str = item.findtext("geo:lat", "", ns)
                    lng_str = item.findtext("geo:long", "", ns)
                    if not lat_str:
                        geo_point = item.find("geo:Point", ns)
                        if geo_point is not None:
                            lat_str = geo_point.findtext("geo:lat", "", ns)
                            lng_str = geo_point.findtext("geo:long", "", ns)

                    lat = float(lat_str) if lat_str else None
                    lng = float(lng_str) if lng_str else None

                    items.append(
                        {
                            "id": _make_id("gdacs-live", title),
                            "title": title,
                            "description": _clean_html(desc)[:300],
                            "url": link,
                            "published_at": _parse_rss_date(pub_date),
                            "alert_level": alert_level.lower()
                            if alert_level
                            else "green",
                            "event_type": event_type,
                            "country": gcountry,
                            "severity": severity_text,
                            "population": population,
                            "lat": lat,
                            "lng": lng,
                        }
                    )
    except (httpx.HTTPError, ET.ParseError, KeyError, ValueError):
        pass

    return items


async def get_crisis_intelligence(
    disaster_name: str,
    country: str,
    disaster_type: str,
    region: str | None = None,
    days_back: int = 90,
    limit: int = 50,
) -> dict:
    """
    Aggregate intelligence from all sources for a specific crisis.
    Returns categorized, scored, and sorted intelligence items.
    """
    reliefweb_task = fetch_reliefweb_reports(
        country, disaster_type, disaster_name, limit=30, days_back=days_back
    )
    gdacs_task = fetch_gdacs_alerts(country, disaster_type, disaster_name)
    news_task = fetch_news_feeds(country, disaster_type, disaster_name)

    results = await asyncio.gather(
        reliefweb_task, gdacs_task, news_task, return_exceptions=True
    )

    all_items = []
    source_stats = {}

    for result in results:
        if isinstance(result, Exception):
            continue
        for item in result:
            all_items.append(item)
            src = item.get("source", "Unknown")
            source_stats[src] = source_stats.get(src, 0) + 1

    all_items.sort(
        key=lambda x: (x.get("relevance_score", 0), x.get("published_at", "")),
        reverse=True,
    )
    all_items = all_items[:limit]

    categories = {}
    for item in all_items:
        cat = item.get("category", "other")
        categories.setdefault(cat, []).append(item)

    return {
        "disaster_name": disaster_name,
        "country": country,
        "disaster_type": disaster_type,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_items": len(all_items),
        "source_breakdown": source_stats,
        "categories": {cat: len(items) for cat, items in categories.items()},
        "items": all_items,
    }


def _clean_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_rss_date(date_str: str) -> str:
    if not date_str:
        return ""
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ]:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
    return date_str
