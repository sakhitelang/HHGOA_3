"""Post retrieval: scrape or fall back to search API metadata."""

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup

from src.search import SearchMatch

TIMEOUT = 10


@dataclass
class PostData:
    url: str
    title: str
    snippet: str
    content: str
    source_api: str

    def canonical_json(self) -> str:
        payload = {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "content": self.content,
            "source_api": self.source_api,
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _try_oembed(url: str) -> Optional[dict]:
    oembed_endpoints = [
        f"https://publish.twitter.com/oembed?url={url}",
        f"https://www.linkedin.com/oembed?url={url}",
    ]
    for endpoint in oembed_endpoints:
        try:
            resp = requests.get(endpoint, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                return resp.json()
        except requests.RequestException:
            continue
    return None


def _try_scrape(url: str) -> Tuple[str, str]:
    try:
        resp = requests.get(
            url,
            timeout=TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"]

        og_desc = soup.find("meta", property="og:description")
        snippet = og_desc["content"] if og_desc and og_desc.get("content") else ""

        # Pull visible text excerpt (not fabricating — whatever the page returns)
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")[:5]]
        content = " ".join(p for p in paragraphs if p)[:2000]

        return title or "", snippet or content[:500]
    except requests.RequestException:
        return "", ""


def retrieve_post_data(match: SearchMatch) -> PostData:
    """
    Pull post content/metadata.
    On scrape failure, hash search API metadata instead of fabricating.
    """
    title = match.title
    snippet = match.snippet
    content = ""

    oembed = _try_oembed(match.url)
    if oembed:
        title = oembed.get("title", title) or title
        content = oembed.get("html", "")[:2000]
        if not snippet:
            snippet = oembed.get("author_name", "")

    if not content:
        scraped_title, scraped_content = _try_scrape(match.url)
        if scraped_title:
            title = scraped_title
        if scraped_content:
            content = scraped_content
            if not snippet:
                snippet = scraped_content[:500]

    # Fallback: use search API metadata (honest, not fabricated)
    if not content and not snippet:
        snippet = f"Search result: {match.title or match.url}"

    return PostData(
        url=match.url,
        title=title,
        snippet=snippet,
        content=content,
        source_api=match.source,
    )
