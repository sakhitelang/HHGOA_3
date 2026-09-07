#!/usr/bin/env python3
"""
Independent verification process — re-fetches post data, re-hashes,
compares against stored chain record. Proves tamper-evidence.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.ui import (
    print_banner,
    print_disclosure,
    stage_header,
    stage_ok,
    stage_fail,
    stage_info,
    print_hash,
    print_result_table,
    print_verdict,
)
from src.search import SearchMatch
from src.scrape import retrieve_post_data
from src.blockchain import SimulatedChain


def main():
    parser = argparse.ArgumentParser(
        description="HH Goa Task 3 — Independent Blockchain Verification"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Social post URL to verify (defaults to latest chain entry)",
    )
    args = parser.parse_args()

    print_banner()
    print_disclosure()

    chain = SimulatedChain()

    if not chain.blocks:
        stage_fail("Chain is empty. Run upload.py first.")
        sys.exit(1)

    if args.url:
        block = chain.find_by_url(args.url)
        if not block:
            stage_fail(f"No chain block found for URL: {args.url}")
            sys.exit(1)
    else:
        block = chain.latest()

    url = block.metadata.get("url", "")
    if not url:
        stage_fail("Latest block has no URL metadata.")
        sys.exit(1)

    stage_header(5, "Independent Re-Verification")
    stage_info(f"Re-fetching: {url}")
    stage_info(f"On-chain block #{block.index} · stored hash below")
    print_hash("Stored data_hash", block.data_hash)

    # Independent re-fetch (separate process, no shared memory with upload.py)
    match = SearchMatch(
        url=url,
        title=block.metadata.get("title", ""),
        snippet=block.metadata.get("snippet", ""),
        source=block.metadata.get("source_api", "verify"),
    )
    post = retrieve_post_data(match)
    recomputed_hash = post.content_hash()

    stage_ok("Post data re-fetched and re-hashed independently")
    print_hash("Recomputed hash", recomputed_hash)

    chain_ok = chain.verify_chain_integrity()
    hash_match = recomputed_hash == block.data_hash
    passed = chain_ok and hash_match

    print()
    print_result_table([
        ("Chain integrity", "All previous_hash links valid", "PASS" if chain_ok else "FAIL"),
        ("Content hash", f"{recomputed_hash[:32]}…", "PASS" if hash_match else "FAIL"),
        ("URL", url, "PASS" if hash_match else "FAIL"),
    ])

    print()
    print_verdict(passed)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
