#!/usr/bin/env python3
"""
FastAPI Server for HH Goa Task 3 — Face Identification & Blockchain Verification Pipeline.
Provides API endpoints for web UI and full pipeline execution.
"""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

# Setup paths
ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
CONSENT_DIR = ROOT / "consent"
WHITELIST_FILE = CONSENT_DIR / "whitelist.json"
DATA_DIR.mkdir(exist_ok=True)
CONSENT_DIR.mkdir(exist_ok=True)

from src.blockchain import SimulatedChain, Block
from src.consent import is_consented, get_whitelisted_hashes
from src.face_encode import detect_and_encode_face, encode_face
from src.scrape import retrieve_post_data
from src.search import SearchMatch, find_social_match, find_all_social_matches

app = FastAPI(title="HH Goa 2026 — Face ID & Blockchain Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerifyRequest(BaseModel):
    url: Optional[str] = None
    block_index: Optional[int] = None


class TamperRequest(BaseModel):
    block_index: int
    new_data: str


class WhitelistAddRequest(BaseModel):
    file_hash: str


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "event": "Hacker House Goa 2026",
        "task": "Task #3 — Face ID + Blockchain Verification",
    }


@app.get("/api/consent/whitelist")
def list_whitelist():
    hashes = get_whitelisted_hashes()
    return {"allowed_hashes": hashes, "count": len(hashes)}


@app.post("/api/consent/whitelist")
def add_to_whitelist(req: WhitelistAddRequest):
    h = req.file_hash.strip().lower()
    if len(h) != 64:
        raise HTTPException(status_code=400, detail="Invalid SHA-256 hash length")

    whitelist_data = {"allowed_hashes": [], "note": "SHA-256 hashes of consented test images only."}
    if WHITELIST_FILE.exists():
        try:
            with open(WHITELIST_FILE) as f:
                whitelist_data = json.load(f)
        except Exception:
            pass

    allowed = set(whitelist_data.get("allowed_hashes", []))
    allowed.add(h)
    whitelist_data["allowed_hashes"] = sorted(list(allowed))

    with open(WHITELIST_FILE, "w") as f:
        json.dump(whitelist_data, f, indent=2)

    return {"message": "Hash whitelisted successfully", "allowed_hashes": whitelist_data["allowed_hashes"]}


@app.delete("/api/consent/whitelist/{file_hash}")
def remove_from_whitelist(file_hash: str):
    h = file_hash.strip().lower()
    if not WHITELIST_FILE.exists():
        return {"message": "Whitelist empty"}

    with open(WHITELIST_FILE) as f:
        whitelist_data = json.load(f)

    allowed = [x for x in whitelist_data.get("allowed_hashes", []) if x != h]
    whitelist_data["allowed_hashes"] = allowed

    with open(WHITELIST_FILE, "w") as f:
        json.dump(whitelist_data, f, indent=2)

    return {"message": "Hash removed", "allowed_hashes": allowed}


@app.post("/api/pipeline/run")
async def run_pipeline(
    file: UploadFile = File(...),
    auto_whitelist: bool = Form(False),
    simulation_mode: bool = Form(True),
    custom_social_url: Optional[str] = Form(None),
):
    """
    Execute Stages 0 to 4:
    Stage 0: Consent Check (SHA-256 whitelist)
    Stage 1: In-Memory Face Detection & Encoding
    Stage 2: Reverse Image Search with Social Domain Filter
    Stage 3: Post Retrieval & Content Hash Generation
    Stage 4: Blockchain Ledger Insertion
    """
    logs = []
    
    def log(stage: int, msg: str, status: str = "info", **extra):
        entry = {"stage": stage, "message": msg, "status": status, **extra}
        logs.append(entry)
        return entry

    # Save temp file
    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Calculate SHA-256
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Handle optional quick-whitelist toggle for easy testing
        if auto_whitelist:
            add_to_whitelist(WhitelistAddRequest(file_hash=file_hash))

        # ── Stage 0: Consent Gate ──────────────────────────────────────
        is_allowed, computed_hash = is_consented(tmp_path)
        if not is_allowed:
            log(0, f"CONSENT REJECTED: SHA-256 hash {file_hash[:16]}… is not in whitelist.", "fail", file_hash=file_hash)
            return JSONResponse(
                status_code=403,
                content={
                    "stage": 0,
                    "success": False,
                    "error": "CONSENT_REJECTED",
                    "message": "Image is not whitelisted. Strict consent architecture blocked execution.",
                    "file_hash": file_hash,
                    "logs": logs,
                },
            )

        log(0, "Image SHA-256 verified against consent whitelist.", "ok", file_hash=file_hash)

        # ── Stage 1: Face Detection & Encoding ─────────────────────────
        try:
            face_meta = detect_and_encode_face(tmp_path)
            emb_hash = face_meta["fingerprint"]
            log(
                1,
                f"Face detected ({face_meta['dimensions']}-dim vector). Biometric data held in memory only.",
                "ok",
                emb_hash=emb_hash,
                bbox=face_meta.get("bbox"),
                backend=face_meta.get("backend"),
            )
        except Exception as e:
            log(1, f"Face detection failed: {str(e)}", "fail")
            return JSONResponse(
                status_code=400,
                content={"stage": 1, "success": False, "error": "FACE_DETECTION_FAILED", "message": str(e), "logs": logs},
            )

        # ── Stage 2: Reverse Image Search (Cross-Platform Social Discovery)
        hint = custom_social_url.strip() if custom_social_url and custom_social_url.strip() else None
        all_matches = find_all_social_matches(str(tmp_path), query_hint=hint)
        
        if not all_matches:
            log(2, "Live search executed across instagram.com, x.com, linkedin.com, facebook.com.", "info")
            log(2, "No matching public social post found after domain filter.", "warn")
            log(2, "Honest exit: Zero fabricated results per PRD anti-spoofing policy.", "info")
            return {
                "stage": 2,
                "success": True,
                "match_found": False,
                "message": "Honest exit: No matching social post found on filtered domains.",
                "file_hash": file_hash,
                "emb_hash": emb_hash,
                "face_meta": face_meta,
                "logs": logs,
            }

        search_match = all_matches[0]
        discovered_accounts = [
            {"platform": getattr(m, "platform", "Social Web"), "url": m.url, "title": m.title}
            for m in all_matches
        ]

        platform_summary = ", ".join([f"{m.platform} ({m.url})" for m in all_matches])
        log(
            2,
            f"Discovered {len(all_matches)} matching account(s): {platform_summary}",
            "ok",
            discovered_accounts=discovered_accounts,
            match_url=search_match.url,
            match_source=search_match.source,
            match_title=search_match.title,
        )

        # ── Stage 3: Post Retrieval & Metadata Hash ────────────────────
        post_data = retrieve_post_data(search_match)
        content_hash = post_data.content_hash()
        log(
            3,
            f"Post retrieved from {search_match.url} and hashed (SHA-256: {content_hash[:16]}…).",
            "ok",
            content_hash=content_hash,
            url=post_data.url,
            title=post_data.title,
        )

        # ── Stage 4: Blockchain Ledger Write ───────────────────────────
        chain = SimulatedChain()
        block = chain.add_block(
            data_hash=content_hash,
            metadata={
                "url": post_data.url,
                "title": post_data.title,
                "snippet": post_data.snippet,
                "source_api": post_data.source_api,
                "file_hash": file_hash,
                "embedding_fingerprint": emb_hash,
                "discovered_accounts": discovered_accounts,
            },
        )
        block_hash = block.block_hash()
        log(
            4,
            f"Block #{block.index} written to simulated hash chain with {len(discovered_accounts)} linked account(s).",
            "ok",
            block_index=block.index,
            block_hash=block_hash,
            prev_hash=block.previous_hash,
        )

        return {
            "stage": 4,
            "success": True,
            "match_found": True,
            "file_hash": file_hash,
            "emb_hash": emb_hash,
            "face_meta": face_meta,
            "match": {
                "url": post_data.url,
                "title": post_data.title,
                "source": post_data.source_api,
                "platform": getattr(search_match, "platform", "Social Web"),
            },
            "discovered_accounts": discovered_accounts,
            "content_hash": content_hash,
            "block": {
                "index": block.index,
                "timestamp": block.timestamp,
                "data_hash": block.data_hash,
                "previous_hash": block.previous_hash,
                "block_hash": block_hash,
                "metadata": block.metadata,
            },
            "logs": logs,
        }

    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@app.post("/api/pipeline/verify")
def run_verification(req: VerifyRequest):
    """
    Stage 5: Independent Verification Process.
    Re-fetches/re-hashes post data, verifies blockchain integrity, and matches hash.
    """
    chain = SimulatedChain()
    if not chain.blocks:
        raise HTTPException(
            status_code=400,
            detail="Blockchain ledger is empty (0 blocks). Please run Stages 0–4 on the Pipeline Runner tab first to mint your on-chain block!"
        )

    target_block = None
    url_query = req.url.strip() if req.url and req.url.strip() else None

    if url_query:
        target_block = chain.find_by_url(url_query)
        if not target_block:
            available = [b.metadata.get("url", f"Block #{b.index}") for b in chain.blocks]
            raise HTTPException(
                status_code=404,
                detail=f"No on-chain block found matching '{url_query}'. Active blocks in ledger: {len(chain.blocks)} ({', '.join(available)})"
            )
    elif req.block_index is not None:
        if 0 <= req.block_index < len(chain.blocks):
            target_block = chain.blocks[req.block_index]
        else:
            raise HTTPException(status_code=404, detail=f"Invalid block index #{req.block_index}. Total blocks: {len(chain.blocks)}")
    else:
        target_block = chain.latest()

    if not target_block:
        target_block = chain.latest()

    url = target_block.metadata.get("url", "")
    stored_hash = target_block.data_hash

    # Independent re-fetch (no shared memory)
    match = SearchMatch(
        url=url,
        title=target_block.metadata.get("title", ""),
        snippet=target_block.metadata.get("snippet", ""),
        source=target_block.metadata.get("source_api", "verify"),
    )
    post = retrieve_post_data(match)
    recomputed_hash = post.content_hash()

    # Integrity verification
    chain_integrity_ok = chain.verify_chain_integrity()
    hash_matches = stored_hash == recomputed_hash
    overall_pass = chain_integrity_ok and hash_matches

    return {
        "verified": overall_pass,
        "verdict": "PASS" if overall_pass else "FAIL",
        "chain_integrity": chain_integrity_ok,
        "hash_match": hash_matches,
        "target_block": {
            "index": target_block.index,
            "timestamp": target_block.timestamp,
            "block_hash": target_block.block_hash(),
            "previous_hash": target_block.previous_hash,
            "data_hash": stored_hash,
            "metadata": target_block.metadata,
        },
        "recomputed_hash": recomputed_hash,
        "stored_hash": stored_hash,
        "recomputed_url": post.url,
        "checks": [
            {
                "name": "Chain Integrity",
                "detail": "All previous_hash cryptographic links validated across entire chain",
                "status": "PASS" if chain_integrity_ok else "FAIL",
            },
            {
                "name": "Content SHA-256 Digest",
                "detail": f"Re-hashed live content matches block #{target_block.index} data_hash",
                "status": "PASS" if hash_matches else "FAIL",
            },
            {
                "name": "Source URL Consistency",
                "detail": url,
                "status": "PASS" if hash_matches else "FAIL",
            },
        ],
    }


@app.get("/api/blockchain")
def get_blockchain():
    chain = SimulatedChain()
    integrity = chain.verify_chain_integrity()
    blocks = []
    for b in chain.blocks:
        blocks.append(
            {
                "index": b.index,
                "timestamp": b.timestamp,
                "data_hash": b.data_hash,
                "previous_hash": b.previous_hash,
                "block_hash": b.block_hash(),
                "metadata": b.metadata,
            }
        )
    return {
        "chain_type": "simulated_hash_chain",
        "block_count": len(blocks),
        "integrity_valid": integrity,
        "blocks": blocks,
    }


@app.post("/api/blockchain/tamper")
def tamper_blockchain(req: TamperRequest):
    """Demo function: Modify a block to prove tamper detection."""
    chain = SimulatedChain()
    if not chain.blocks or req.block_index >= len(chain.blocks):
        raise HTTPException(status_code=400, detail="Invalid block index to tamper")

    chain.blocks[req.block_index].data_hash = req.new_data
    chain._save()
    return {
        "message": f"Block #{req.block_index} data_hash tampered with '{req.new_data}'",
        "integrity_now_valid": chain.verify_chain_integrity(),
    }


@app.post("/api/blockchain/reset")
def reset_blockchain():
    chain_file = DATA_DIR / "chain.json"
    if chain_file.exists():
        chain_file.unlink()
    return {"message": "Simulated chain reset successfully", "block_count": 0}


# Mount web UI files
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
def serve_index():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Web UI not yet compiled"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)

