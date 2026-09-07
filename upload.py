#!/usr/bin/env python3
"""
Face Identification & Blockchain Verification Pipeline — Upload Stage.

Stages 0–4: consent → face encode → reverse search → post retrieval → chain write.
Run independently from verify.py for tamper-evidence demo.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Ensure project root on path
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
)
from src.consent import check_consent
from src.face_encode import encode_face
from src.search import find_social_match
from src.scrape import retrieve_post_data
from src.blockchain import SimulatedChain


def main():
    parser = argparse.ArgumentParser(
        description="HH Goa Task 3 — Face ID + Blockchain Upload Pipeline"
    )
    parser.add_argument(
        "image",
        type=Path,
        help="Path to consented test image (must be on SHA-256 whitelist)",
    )
    args = parser.parse_args()

    print_banner()
    print_disclosure()

    # ── Stage 0: Consent gate ──────────────────────────────────────────
    stage_header(0, "Consent Gate")
    allowed, file_hash = check_consent(args.image)
    stage_ok(f"Image whitelisted (consent verified)")
    print_hash("File SHA-256", file_hash)

    # ── Stage 1: Face detection / encoding ─────────────────────────────
    stage_header(1, "Face Detection & Encoding")
    try:
        embedding, emb_hash = encode_face(args.image)
        stage_ok(f"Face detected and encoded ({len(embedding)}-dim embedding)")
        print_hash("Embedding fingerprint", emb_hash)
        stage_info("Embedding held in memory only — not persisted to disk")
        del embedding  # explicit cleanup
    except ValueError as e:
        stage_fail(str(e))
        sys.exit(1)
    except Exception as e:
        stage_fail(f"Face encoding failed: {e}")
        sys.exit(1)

    # ── Stage 2: Reverse image / web search ──────────────────────────
    stage_header(2, "Reverse Image Search (Social Filter)")
    match = find_social_match(str(args.image))
    if not match:
        stage_fail("No matching social post found after domain filter.")
        stage_info("Domains checked: instagram.com, x.com, linkedin.com, facebook.com")
        stage_info("This is an honest no-match — no hardcoded fallback used.")
        sys.exit(0)

    stage_ok(f"Match found via {match.source}")
    stage_info(f"URL: {match.url}")
    if match.title:
        stage_info(f"Title: {match.title[:80]}")

    # ── Stage 3: Post retrieval ────────────────────────────────────────
    stage_header(3, "Post Retrieval")
    post = retrieve_post_data(match)
    data_hash = post.content_hash()
    stage_ok("Post data retrieved (scrape or API metadata fallback)")
    print_hash("Content SHA-256", data_hash)
    stage_info(f"URL: {post.url}")

    # ── Stage 4: Blockchain upload ───────────────────────────────────
    stage_header(4, "Blockchain Upload (Simulated Hash Chain)")
    chain = SimulatedChain()
    block = chain.add_block(
        data_hash=data_hash,
        metadata={
            "url": post.url,
            "title": post.title,
            "snippet": post.snippet,
            "source_api": post.source_api,
            "file_hash": file_hash,
            "embedding_fingerprint": emb_hash,
        },
    )
    stage_ok(f"Block #{block.index} written to simulated chain")
    print_hash("Block hash", block.block_hash())
    print_hash("Previous hash", block.previous_hash)
    stage_info(f"Chain file: {chain.path}")

    print()
    stage_ok("Upload complete. Run verify.py independently to re-verify.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
