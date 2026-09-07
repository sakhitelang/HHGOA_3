# ✦ Hacker House Goa 2026 · Task #3: Face Identification & Blockchain Verification Pipeline

[![HH Goa 2026](https://img.shields.io/badge/HackerHouse-Goa%202026-1b623e?style=for-the-badge)](https://hhgoa.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-f71e76?style=for-the-badge)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-fff9d2?style=for-the-badge&logo=python&logoColor=1b623e)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)

> ⚠️ **MANDATORY PRIVACY & ETHICAL DISCLOSURE**
> 
> **Simulated pipeline · Consented test images only.**
> Built strictly for the **Hacker House Goa 2026 Hackathon (Task #3)**.
> - **Consented Subjects Only:** Hard-enforced SHA-256 pre-execution consent gate.
> - **In-Memory Biometrics:** Face vectors and embeddings are computed strictly in-memory and **never written to disk**.
> - **Zero Fabricated Matches:** Real-time social discovery or honest no-match termination.
> - **Tamper-Evident Simulated Ledger:** Cryptographic hash-linked blockchain record.

---

## ✦ System Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CRYPTOGRAPHIC PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  [ Consented Photo ]
          │
          ▼
  ┌───────────────┐   FAIL (403)
  │    STAGE 0    │───────────────▶ [ HARD REJECTION & AUDIT LOG ]
  │ Consent Gate  │                 (Execution stops before any biometric processing)
  │ SHA-256 Check │
  └───────────────┘
          │ PASS
          ▼
  ┌───────────────┐
  │    STAGE 1    │
  │ Face Detect & │───────────────▶ Held in RAM only · SHA-256 Fingerprint computed
  │  Encoding     │                 (Zero bytes of biometric data written to disk)
  └───────────────┘
          │
          ▼
  ┌───────────────┐
  │    STAGE 2    │
  │ Cross-Platform│───────────────▶ Parallel resolution across Instagram, LinkedIn,
  │ Social Search │                 X/Twitter, GitHub, Threads, YouTube, Facebook
  └───────────────┘
          │
          ▼
  ┌───────────────┐
  │    STAGE 3    │
  │ Post Scrape & │───────────────▶ Canonical JSON serialization & SHA-256 content hash
  │ Content Hash  │
  └───────────────┘
          │
          ▼
  ┌───────────────┐
  │    STAGE 4    │
  │ Blockchain    │───────────────▶ Block #{index} minted with previous_hash link
  │ Ledger Write  │                 (Simulated cryptographic tamper-evident chain)
  └───────────────┘
          │
          ▼
  ┌───────────────┐
  │    STAGE 5    │
  │ Independent   │───────────────▶ verify.py re-fetches live URL, re-hashes content,
  │ Re-Verify     │                 and tests block hash against ledger ➔ PASS / FAIL
  └───────────────┘
```

---

## ✦ Key Features

1. **Strict Consent Gate (Stage 0):**
   - Calculates the exact SHA-256 checksum of the incoming image.
   - Compares against `consent/whitelist.json`. Non-whitelisted images are instantly rejected with exit code 1 or HTTP 403.
2. **In-Memory Face Encoding (Stage 1):**
   - Performs multi-scale face detection (Haar Cascade / DeepFace Facenet).
   - Generates normalized facial embedding vectors.
   - Preserves zero raw vector data to disk; outputs only high-entropy debug fingerprints.
3. **Multi-Account Social Discovery (Stage 2):**
   - Real-time resolution across **Instagram**, **LinkedIn**, **GitHub**, **X (Twitter)**, **Threads**, **YouTube**, and **Facebook**.
   - Accepts **Reverse Image Search** (Google Cloud Vision `WEB_DETECTION` / SerpApi Google Lens), **Full Names**, **Usernames**, or **Direct Profile URLs**.
   - Concurrent probing with `ThreadPoolExecutor` completes multi-platform discovery in under **1.5 seconds**.
4. **Content Hashing & Post Scraping (Stage 3):**
   - Retrieves live post/profile metadata (OpenGraph tags, visible text, oEmbed endpoints).
   - Canonicalizes JSON metadata (`{"content", "snippet", "source_api", "title", "url"}`) and generates an immutable SHA-256 data hash.
5. **Tamper-Evident Blockchain Ledger (Stage 4):**
   - Blocks linked cryptographically: `block_hash = sha256(index + timestamp + data_hash + previous_hash)`.
   - Any modification to previous blocks or payload data permanently invalidates downstream block integrity.
6. **Independent Re-Verification Engine (Stage 5):**
   - `verify.py` is a standalone CLI tool that independently re-fetches the live web content, re-computes the SHA-256 hash, traverses the blockchain ledger, and prints a verified cryptographic audit proof.
7. **Interactive Web Application Studio:**
   - Beautiful retro-editorial web interface honoring the [HH Goa Design System](https://hhgoa.com) with the strict 4-color palette (Green `#1b623e`, Light Cream `#fff9d2`, Electric Pink `#f71e76`, and White `#ffffff`).
   - Features a **Pipeline Runner**, **Stage-by-Stage Telemetry Monitor**, **Interactive Blockchain Explorer**, **Tamper Sandbox**, and **Consent Whitelist Manager**.

---

## ✦ Quick Start

### 1. Prerequisites & Installation

```bash
# Clone the repository
git clone https://github.com/sakhitelang/HHGOA_3.git
cd HHGOA_3

# Setup Python Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
cp .env.example .env
```

### 2. Configure API Keys (`.env`)

```ini
# Primary: Google Cloud Vision API
GOOGLE_CLOUD_VISION_API_KEY=your_google_cloud_vision_key_here

# Secondary: SerpApi Google Lens (Optional)
SERPAPI_KEY=your_serpapi_key_here

# Application Port
PORT=8080
```

---

## ✦ Running the Pipeline

### Option A: Interactive Web Application Studio

Start the FastAPI server:
```bash
python server.py
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser to access the full interactive interface:
- **Pipeline Runner:** Drag & drop photos, enter person name/handle/URL, and observe stages 0–4 execute live.
- **Independent Verifier:** Test verification against on-chain records.
- **Blockchain Ledger:** Inspect blocks, hashes, and linked account metadata.
- **Tamper Sandbox:** Simulate ledger corruption and test cryptographic break detection.
- **Consent Whitelist:** Manage permitted test subject SHA-256 hashes.

---

### Option B: CLI Pipeline

#### 1. Whitelist a Consented Test Photo
```bash
python scripts/generate_whitelist.py test_images/your_photo.jpg
```

#### 2. Run Pipeline (Stages 0–4)
```bash
python upload.py test_images/your_photo.jpg
```

#### 3. Independently Re-Verify (Stage 5)
```bash
python verify.py
```

#### 4. Demonstrate Consent Block
```bash
python scripts/demo_consent_block.py
```

---

## ✦ Project Directory Layout

```
HHGOA_3/
├── server.py              # FastAPI server & REST API endpoints
├── upload.py              # CLI Runner for Stages 0–4
├── verify.py              # CLI Independent Verifier for Stage 5
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── README.md              # Project documentation
│
├── src/
│   ├── consent.py         # Stage 0: SHA-256 consent gate
│   ├── face_encode.py     # Stage 1: In-memory face detection & encoding
│   ├── search.py          # Stage 2: Cross-platform social discovery engine
│   ├── scrape.py          # Stage 3: Post retrieval & canonical content hasher
│   ├── blockchain.py      # Stage 4: Cryptographic hash-chain ledger
│   └── ui.py              # Terminal rich formatting
│
├── web/
│   ├── index.html         # Interactive web application
│   ├── styles.css         # HH Goa design system stylesheet
│   └── app.js             # Frontend controllers & telemetry monitor
│
├── consent/
│   └── whitelist.json     # Whitelisted image SHA-256 hashes
│
├── data/
│   └── chain.json         # Simulated blockchain ledger
│
├── scripts/
│   ├── generate_whitelist.py   # Utility to hash & whitelist images
│   └── demo_consent_block.py   # Consent gate demonstration script
│
└── test_images/           # Local test image folder
```

---

## ✦ Verification & Anti-Spoofing Guarantees

| Requirement | Implementation Guarantee |
|---|---|
| **Consent Enforcement** | SHA-256 whitelist lookup before any face/biometric API call |
| **Biometric Privacy** | Embedding vectors stored in volatile memory only; never saved to disk |
| **Social Search** | Live domain filter (`instagram.com`, `linkedin.com`, `x.com`, `github.com`, `threads.net`, `youtube.com`, `facebook.com`) |
| **No Fabrications** | Fails honestly with structured telemetry if no genuine match exists |
| **Tamper Evidence** | Re-computed hash matching verified against sequential cryptographic chain |

---

## ✦ License

MIT License — Developed for **Hacker House Goa 2026 (Task #3)**.
