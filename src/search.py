"""Reverse image & cross-platform social account search with domain filter."""

import base64
import json
import os
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup

TIMEOUT = 8

SOCIAL_DOMAINS = {
    "instagram.com",
    "www.instagram.com",
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "linkedin.com",
    "www.linkedin.com",
    "in.linkedin.com",
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "github.com",
    "www.github.com",
    "threads.net",
    "www.threads.net",
    "threads.com",
    "www.threads.com",
    "youtube.com",
    "www.youtube.com",
}


@dataclass
class SearchMatch:
    url: str
    title: str
    snippet: str
    source: str  # "google_vision" | "serpapi" | "social_profile_lookup" | "web_discovery"
    platform: str = "Social Web"


def _domain_ok(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        roots = {
            "instagram.com",
            "twitter.com",
            "x.com",
            "linkedin.com",
            "facebook.com",
            "github.com",
            "threads.net",
            "threads.com",
            "youtube.com",
        }
        return any(host == root or host.endswith("." + root) for root in roots)
    except Exception:
        return False


def _detect_platform(url: str) -> str:
    u = url.lower()
    if "instagram.com" in u:
        return "Instagram"
    elif "x.com" in u or "twitter.com" in u:
        return "X / Twitter"
    elif "linkedin.com" in u:
        return "LinkedIn"
    elif "github.com" in u:
        return "GitHub"
    elif "threads.net" in u or "threads.com" in u:
        return "Threads"
    elif "youtube.com" in u or "youtu.be" in u:
        return "YouTube"
    elif "facebook.com" in u:
        return "Facebook"
    return "Social Web"


def _filter_social(results: list[SearchMatch]) -> list[SearchMatch]:
    return [r for r in results if _domain_ok(r.url)]


def _extract_handle_from_url(url: str) -> Optional[str]:
    """Extract clean username/handle from any social URL."""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if not path:
            return None
        parts = [p for p in path.split("/") if p]
        if not parts:
            return None
        
        netloc = parsed.netloc.lower()
        if "linkedin.com" in netloc:
            # e.g. /in/username
            if len(parts) >= 2 and parts[0] in ("in", "pub"):
                return parts[1]
            return parts[-1]
        elif "youtube.com" in netloc:
            # e.g. /@username
            return parts[0].lstrip("@")
        elif "threads.net" in netloc or "threads.com" in netloc:
            return parts[0].lstrip("@")
        elif "instagram.com" in netloc:
            # ignore standard paths like /p/, /reel/, /stories/
            if parts[0] in ("p", "reel", "reels", "stories", "explore", "accounts"):
                return None
            return parts[0]
        else:
            return parts[0].lstrip("@")
    except Exception:
        return None


def _search_web_for_social_profiles(query: str) -> list[SearchMatch]:
    """
    Query public web indices (DuckDuckGo HTML) to find real verified social profiles
    for a given person's name or handle.
    """
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip()
    search_q = f"{q} (site:instagram.com OR site:linkedin.com/in/ OR site:x.com OR site:twitter.com OR site:github.com OR site:threads.net OR site:facebook.com)"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    results: list[SearchMatch] = []
    seen: set[str] = set()

    try:
        r = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": search_q},
            headers=headers,
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # DuckDuckGo HTML results
            for result_elem in soup.find_all("div", class_="result"):
                link_tag = result_elem.find("a", class_="result__url")
                title_tag = result_elem.find("a", class_="result__title")
                snippet_tag = result_elem.find("a", class_="result__snippet")

                if link_tag and link_tag.get("href"):
                    raw_href = link_tag.get("href", "").strip()
                    # Handle DDG redirect URLs /uddg/
                    if "duckduckgo.com/l/?uddg=" in raw_href:
                        parsed = urllib.parse.urlparse(raw_href)
                        params = urllib.parse.parse_qs(parsed.query)
                        if "uddg" in params:
                            raw_href = unquote(params["uddg"][0])

                    if _domain_ok(raw_href) and raw_href not in seen:
                        seen.add(raw_href)
                        title = title_tag.get_text(strip=True) if title_tag else f"{q} Profile"
                        snippet = snippet_tag.get_text(strip=True) if snippet_tag else f"Public profile for {q}"
                        plat = _detect_platform(raw_href)
                        results.append(
                            SearchMatch(
                                url=raw_href,
                                title=title,
                                snippet=snippet,
                                source="web_discovery",
                                platform=plat,
                            )
                        )
    except Exception as e:
        print(f"[SEARCH] Public web search exception: {e}", file=sys.stderr)

    return results


def resolve_all_social_accounts(query: str) -> list[SearchMatch]:
    """
    Find all accounts a person has across platforms given a name, handle, or URL:
    - Instagram
    - X / Twitter
    - LinkedIn
    - GitHub
    - Threads
    - YouTube
    - Facebook
    """
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip()
    found: list[SearchMatch] = []
    seen: set[str] = set()

    # Case 1: If an explicit URL was provided directly (e.g. an Instagram / LinkedIn / GitHub / X profile)
    if q.startswith("http://") or q.startswith("https://") or any(d in q for d in ["instagram.com", "x.com", "twitter.com", "linkedin.com", "github.com", "threads.net", "facebook.com", "youtube.com"]):
        if not (q.startswith("http://") or q.startswith("https://")):
            full_url = "https://" + q.lstrip("/")
        else:
            full_url = q

        plat = _detect_platform(full_url)
        clean_handle = _extract_handle_from_url(full_url) or full_url.rstrip("/").split("/")[-1].split("?")[0]
        
        seen.add(full_url)
        found.append(
            SearchMatch(
                url=full_url,
                title=f"User provided {plat} profile: @{clean_handle}",
                snippet=f"Verified direct profile provided for @{clean_handle} on {plat}",
                source="social_profile_lookup",
                platform=plat,
            )
        )
        # Use extracted clean handle for cross-referencing other platforms
        candidate_handles = [clean_handle]
    else:
        # Case 2: Name or Handle entered
        clean = q.lstrip("@").strip()
        candidate_handles = []
        if " " in clean:
            # Full name e.g. "Sakhi Telang"
            compact = clean.replace(" ", "").lower()
            snake = clean.replace(" ", "_").lower()
            hyphen = clean.replace(" ", "-").lower()
            dot = clean.replace(" ", ".").lower()
            candidate_handles.extend([compact, snake, hyphen, dot])
        else:
            candidate_handles.append(clean)

    # 1. Run live public web discovery for this name/handle
    web_matches = _search_web_for_social_profiles(q)
    for wm in web_matches:
        if wm.url not in seen:
            seen.add(wm.url)
            found.append(wm)

    # 2. Check direct candidate URLs across major platforms concurrently
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    }

    from concurrent.futures import ThreadPoolExecutor, as_completed

    tasks = []
    for h in candidate_handles[:3]:
        candidates = [
            ("Instagram", f"https://www.instagram.com/{h}/", f"@{h} on Instagram"),
            ("X / Twitter", f"https://x.com/{h}", f"@{h} on X (Twitter)"),
            ("LinkedIn", f"https://www.linkedin.com/in/{h}", f"@{h} on LinkedIn"),
            ("GitHub", f"https://github.com/{h}", f"@{h} on GitHub"),
            ("Threads", f"https://www.threads.net/@{h}", f"@{h} on Threads"),
            ("YouTube", f"https://www.youtube.com/@{h}", f"@{h} on YouTube"),
            ("Facebook", f"https://www.facebook.com/{h}", f"@{h} on Facebook"),
        ]
        for p_name, t_url, t_title in candidates:
            if t_url not in seen:
                tasks.append((p_name, t_url, t_title, h))

    def _check_url(p_name: str, target_url: str, t_title: str, handle_str: str) -> Optional[SearchMatch]:
        try:
            r = requests.get(target_url, headers=headers, timeout=4, allow_redirects=True)
            # 200, 301, 302, 307, 308, or 999 (LinkedIn bot guard for valid profiles)
            if r.status_code in (200, 301, 302, 307, 308, 999):
                return SearchMatch(
                    url=target_url,
                    title=t_title,
                    snippet=f"Discovered active {p_name} profile for @{handle_str}",
                    source="social_profile_lookup",
                    platform=p_name,
                )
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=16) as executor:
        future_map = {executor.submit(_check_url, p, u, t, h): u for p, u, t, h in tasks}
        for fut in as_completed(future_map):
            res = fut.result()
            if res and res.url not in seen:
                seen.add(res.url)
                found.append(res)

    return found


def search_google_vision(image_path: str) -> list[SearchMatch]:
    """Primary: Google Cloud Vision WEB_DETECTION."""
    api_key = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not api_key and not creds_path:
        return []

    with open(image_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")

    matches: list[SearchMatch] = []
    seen: set[str] = set()

    try:
        if api_key:
            url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
            payload = {
                "requests": [
                    {
                        "image": {"content": content},
                        "features": [{"type": "WEB_DETECTION", "maxResults": 30}],
                    }
                ]
            }
            resp = requests.post(url, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            annotations = resp.json()["responses"][0].get("webDetection", {})
        else:
            from google.cloud import vision

            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=base64.b64decode(content))
            response = client.web_detection(image=image, timeout=TIMEOUT)
            wd = response.web_detection
            annotations = {
                "pagesWithMatchingImages": [
                    {"url": p.url, "pageTitle": getattr(p, "page_title", "")}
                    for p in (wd.pages_with_matching_images or [])
                ],
                "fullMatchingImages": [{"url": i.url} for i in (wd.full_matching_images or [])],
                "partialMatchingImages": [{"url": i.url} for i in (wd.partial_matching_images or [])],
                "bestGuessLabels": [{"label": getattr(b, "label", "")} for b in (wd.best_guess_labels or [])],
                "webEntities": [{"description": getattr(e, "description", "")} for e in (wd.web_entities or [])],
            }

        # Pages with matching images
        for page in annotations.get("pagesWithMatchingImages", []):
            u = page.get("url", "")
            if u and u not in seen:
                seen.add(u)
                matches.append(
                    SearchMatch(
                        url=u,
                        title=page.get("pageTitle", ""),
                        snippet="Google Vision Web Match",
                        source="google_vision",
                        platform=_detect_platform(u),
                    )
                )

        # Entity-based social resolution
        entities = []
        for bg in annotations.get("bestGuessLabels", []):
            if bg.get("label"):
                entities.append(bg["label"])
        for ent in annotations.get("webEntities", []):
            if ent.get("description"):
                entities.append(ent["description"])

        for entity in entities[:2]:
            for sm in resolve_all_social_accounts(entity):
                if sm.url not in seen:
                    seen.add(sm.url)
                    matches.append(sm)

    except Exception as e:
        print(f"[SEARCH] Google Vision lookup failed: {e}", file=sys.stderr)

    return matches


def search_serpapi(image_path: str) -> list[SearchMatch]:
    """Secondary: SerpApi Google Lens reverse image search."""
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    matches: list[SearchMatch] = []
    seen: set[str] = set()

    try:
        resp = requests.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_lens",
                "url": f"data:image/jpeg;base64,{b64}",
                "api_key": api_key,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("visual_matches", []):
            u = item.get("link", "")
            if u and u not in seen:
                seen.add(u)
                matches.append(
                    SearchMatch(
                        url=u,
                        title=item.get("title", ""),
                        snippet=item.get("source", ""),
                        source="serpapi",
                        platform=_detect_platform(u),
                    )
                )
    except Exception as e:
        print(f"[SEARCH] SerpApi lookup failed: {e}", file=sys.stderr)

    return matches


def find_all_social_matches(image_path: str, query_hint: Optional[str] = None) -> list[SearchMatch]:
    """
    Search and discover all matching accounts for the person across platforms.
    """
    all_results: list[SearchMatch] = []
    seen_urls: set[str] = set()

    has_vision = bool(os.getenv("GOOGLE_CLOUD_VISION_API_KEY") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    has_serp = bool(os.getenv("SERPAPI_KEY"))

    if has_vision:
        for r in search_google_vision(image_path):
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                all_results.append(r)

    if has_serp:
        for r in search_serpapi(image_path):
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                all_results.append(r)

    if query_hint:
        for sm in resolve_all_social_accounts(query_hint):
            if sm.url not in seen_urls:
                seen_urls.add(sm.url)
                all_results.append(sm)

    # Check filename stem for handle or name
    stem = Path(image_path).stem.replace("_", " ").replace("-", " ")
    clean_stem = re.sub(r"[0-9]+", "", stem).strip()
    if len(clean_stem) >= 3 and clean_stem.lower() not in {"image", "upload", "photo", "img", "demo", "test"}:
        for sm in resolve_all_social_accounts(clean_stem):
            if sm.url not in seen_urls:
                seen_urls.add(sm.url)
                all_results.append(sm)

    return _filter_social(all_results)


def find_social_match(image_path: str, query_hint: Optional[str] = None) -> Optional[SearchMatch]:
    """
    Backward-compatible single match selector.
    """
    matches = find_all_social_matches(image_path, query_hint)
    return matches[0] if matches else None

