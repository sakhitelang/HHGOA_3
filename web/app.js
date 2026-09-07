/**
 * HH GOA 2026 — Face ID & Blockchain Verification Pipeline Frontend
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentFile = null;
  let currentFileHash = "";
  let whitelistedHashes = [];
  let isRunning = false;
  let latestMintedUrl = "";

  // DOM Elements - Navigation & Theme
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const chainCountBadge = document.getElementById("chainCountBadge");

  // DOM Elements - Stage 0-4 Runner
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const dropzonePrompt = document.getElementById("dropzonePrompt");
  const previewContainer = document.getElementById("previewContainer");
  const faceCanvas = document.getElementById("faceCanvas");
  const scanLine = document.getElementById("scanLine");
  const previewFilename = document.getElementById("previewFilename");
  const previewSize = document.getElementById("previewSize");
  const hashCard = document.getElementById("hashCard");
  const computedFileHashEl = document.getElementById("computedFileHash");
  const hashWhitelistBadge = document.getElementById("hashWhitelistBadge");
  const autoWhitelistCheck = document.getElementById("autoWhitelistCheck");
  const btnRunPipeline = document.getElementById("btnRunPipeline");
  const btnResetUpload = document.getElementById("btnResetUpload");
  const btnSampleValid = document.getElementById("btnSampleValid");
  const btnSampleInvalid = document.getElementById("btnSampleInvalid");
  const uploadSuccessCallout = document.getElementById("uploadSuccessCallout");
  const btnGoToVerify = document.getElementById("btnGoToVerify");

  // DOM Elements - Stepper Cards
  const stepCards = [
    document.getElementById("stepCard0"),
    document.getElementById("stepCard1"),
    document.getElementById("stepCard2"),
    document.getElementById("stepCard3"),
    document.getElementById("stepCard4"),
  ];
  const stepBadges = [
    document.getElementById("stepBadge0"),
    document.getElementById("stepBadge1"),
    document.getElementById("stepBadge2"),
    document.getElementById("stepBadge3"),
    document.getElementById("stepBadge4"),
  ];
  const stepDetails = [
    document.getElementById("stepDetail0"),
    document.getElementById("stepDetail1"),
    document.getElementById("stepDetail2"),
    document.getElementById("stepDetail3"),
    document.getElementById("stepDetail4"),
  ];

  // DOM Elements - Terminal
  const termLogs = document.getElementById("termLogs");
  const btnClearLogs = document.getElementById("btnClearLogs");

  // DOM Elements - Stage 5 Verifier
  const verifyUrlInput = document.getElementById("verifyUrlInput");
  const btnTriggerVerify = document.getElementById("btnTriggerVerify");
  const verifyResultBox = document.getElementById("verifyResultBox");
  const verdictBanner = document.getElementById("verdictBanner");
  const verdictIcon = document.getElementById("verdictIcon");
  const verdictTitle = document.getElementById("verdictTitle");
  const verdictSub = document.getElementById("verdictSub");
  const auditTableBody = document.getElementById("auditTableBody");
  const storedHashVal = document.getElementById("storedHashVal");
  const recomputedHashVal = document.getElementById("recomputedHashVal");

  // DOM Elements - Blockchain Explorer
  const blockchainRibbon = document.getElementById("blockchainRibbon");
  const emptyChainMsg = document.getElementById("emptyChainMsg");
  const chainIntegrityPill = document.getElementById("chainIntegrityPill");
  const btnResetChain = document.getElementById("btnResetChain");
  const blockInspector = document.getElementById("blockInspector");
  const inspectorHeader = document.getElementById("inspectorHeader");
  const inspectorJson = document.getElementById("inspectorJson");

  // DOM Elements - Tamper Sandbox
  const tamperBlockSelect = document.getElementById("tamperBlockSelect");
  const tamperNewData = document.getElementById("tamperNewData");
  const btnInjectTamper = document.getElementById("btnInjectTamper");
  const tamperStatusLog = document.getElementById("tamperStatusLog");
  const btnVerifyTamper = document.getElementById("btnVerifyTamper");

  // DOM Elements - Whitelist Manager
  const newWhitelistHash = document.getElementById("newWhitelistHash");
  const btnAddHash = document.getElementById("btnAddHash");
  const whitelistCount = document.getElementById("whitelistCount");
  const whitelistItems = document.getElementById("whitelistItems");

  // =========================================================================
  // Navigation Tabs
  // =========================================================================
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${targetTab}`).classList.add("active");

      if (targetTab === "explorer") fetchBlockchain();
      if (targetTab === "tamper") populateTamperSelect();
      if (targetTab === "whitelist") fetchWhitelist();
      if (targetTab === "verifier" && !verifyUrlInput.value.trim() && latestMintedUrl) {
        verifyUrlInput.value = latestMintedUrl;
      }
    });
  });

  btnGoToVerify.addEventListener("click", () => {
    if (latestMintedUrl) {
      verifyUrlInput.value = latestMintedUrl;
    }
    document.querySelector('[data-tab="verifier"]').click();
  });

  // =========================================================================
  // Logger Helper
  // =========================================================================
  function log(msg, type = "info") {
    const d = new Date().toLocaleTimeString();
    const line = document.createElement("div");
    line.className = `log-line ${type}`;
    line.textContent = `[${d}] ${msg}`;
    termLogs.appendChild(line);
    termLogs.scrollTop = termLogs.scrollHeight;
  }

  btnClearLogs.addEventListener("click", () => {
    termLogs.innerHTML = "";
    log("Terminal cleared.", "info");
  });

  // =========================================================================
  // SHA-256 Calculation Helper
  // =========================================================================
  async function computeSHA256(file) {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  // =========================================================================
  // Whitelist API Handling
  // =========================================================================
  async function fetchWhitelist() {
    try {
      const res = await fetch("/api/consent/whitelist");
      const data = await res.json();
      whitelistedHashes = data.allowed_hashes || [];
      whitelistCount.textContent = whitelistedHashes.length;
      renderWhitelistItems();
      checkCurrentFileConsent();
    } catch (e) {
      log(`Failed to fetch whitelist: ${e.message}`, "fail");
    }
  }

  function renderWhitelistItems() {
    if (!whitelistedHashes.length) {
      whitelistItems.innerHTML = '<div class="empty-list-msg">No hashes currently whitelisted.</div>';
      return;
    }
    whitelistItems.innerHTML = "";
    whitelistedHashes.forEach((h) => {
      const row = document.createElement("div");
      row.className = "whitelist-item-row";
      row.innerHTML = `
        <span class="whitelist-hash-text">${h}</span>
        <button class="del-hash-btn" data-hash="${h}" title="Remove from whitelist">✕</button>
      `;
      row.querySelector(".del-hash-btn").addEventListener("click", async () => {
        await deleteWhitelistHash(h);
      });
      whitelistItems.appendChild(row);
    });
  }

  async function deleteWhitelistHash(h) {
    try {
      await fetch(`/api/consent/whitelist/${h}`, { method: "DELETE" });
      log(`Removed hash ${h.slice(0, 16)}… from whitelist.`, "warn");
      fetchWhitelist();
    } catch (e) {
      log(`Delete failed: ${e.message}`, "fail");
    }
  }

  btnAddHash.addEventListener("click", async () => {
    const val = newWhitelistHash.value.trim().toLowerCase();
    if (val.length !== 64) {
      alert("Please enter a valid 64-character SHA-256 hash.");
      return;
    }
    try {
      const res = await fetch("/api/consent/whitelist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_hash: val }),
      });
      if (!res.ok) throw new Error("Failed to add hash");
      newWhitelistHash.value = "";
      log(`Added hash ${val.slice(0, 16)}… to consent whitelist.`, "ok");
      fetchWhitelist();
    } catch (e) {
      log(`Add hash failed: ${e.message}`, "fail");
    }
  });

  function checkCurrentFileConsent() {
    if (!currentFileHash) return;
    const isAllowed = whitelistedHashes.includes(currentFileHash.toLowerCase());
    if (isAllowed) {
      hashWhitelistBadge.className = "whitelist-status-badge allowed";
      hashWhitelistBadge.textContent = "✓ CONSENT VERIFIED · WHITELISTED";
      btnRunPipeline.disabled = false;
    } else {
      hashWhitelistBadge.className = "whitelist-status-badge rejected";
      hashWhitelistBadge.textContent = "✗ NOT WHITELISTED · STAGE 0 REJECTION";
      btnRunPipeline.disabled = false; // keep clickable so users can test Stage 0 failure
    }
  }

  // =========================================================================
  // Drag & Drop / File Selection
  // =========================================================================
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) {
      handleSelectedFile(e.target.files[0]);
    }
  });

  async function handleSelectedFile(file) {
    if (!file.type.startsWith("image/")) {
      alert("Please upload a valid image file (JPEG/PNG).");
      return;
    }
    currentFile = file;
    previewFilename.textContent = file.name;
    previewSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;

    // Compute SHA-256
    computedFileHashEl.textContent = "Calculating SHA-256...";
    hashCard.style.display = "block";
    currentFileHash = await computeSHA256(file);
    computedFileHashEl.textContent = currentFileHash;

    // Draw preview on Canvas
    const img = new Image();
    img.onload = () => {
      faceCanvas.width = img.width;
      faceCanvas.height = img.height;
      const ctx = faceCanvas.getContext("2d");
      ctx.drawImage(img, 0, 0);
      dropzonePrompt.style.display = "none";
      previewContainer.style.display = "block";
      btnResetUpload.style.display = "inline-block";
    };
    img.src = URL.createObjectURL(file);

    resetStepper();
    uploadSuccessCallout.style.display = "none";
    log(`Selected file: ${file.name} (SHA-256: ${currentFileHash.slice(0, 16)}…)`, "info");
    checkCurrentFileConsent();
  }

  btnResetUpload.addEventListener("click", () => {
    currentFile = null;
    currentFileHash = "";
    fileInput.value = "";
    dropzonePrompt.style.display = "block";
    previewContainer.style.display = "none";
    hashCard.style.display = "none";
    btnResetUpload.style.display = "none";
    btnRunPipeline.disabled = true;
    uploadSuccessCallout.style.display = "none";
    resetStepper();
    log("Reset upload studio.", "info");
  });

  // =========================================================================
  // Sample Images Generator / Loaders
  // =========================================================================
  async function createSampleCanvasImage(text, isWhitelisted) {
    const canvas = document.createElement("canvas");
    canvas.width = 300;
    canvas.height = 300;
    const ctx = canvas.getContext("2d");

    // Retro sand/green gradient
    ctx.fillStyle = isWhitelisted ? "#1a4d2e" : "#801212";
    ctx.fillRect(0, 0, 300, 300);

    // Draw Face Outline
    ctx.strokeStyle = "#f5c518";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(150, 130, 60, 0, Math.PI * 2); // head
    ctx.stroke();

    // Eyes & Smile
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(130, 120, 8, 0, Math.PI * 2);
    ctx.arc(170, 120, 8, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(150, 140, 24, 0.2 * Math.PI, 0.8 * Math.PI);
    ctx.stroke();

    // Text Label
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 13px 'JetBrains Mono', monospace";
    ctx.textAlign = "center";
    ctx.fillText(text, 150, 240);
    ctx.fillText(isWhitelisted ? "CONSENTED TEST SUBJECT" : "NON-WHITELISTED TEST", 150, 260);

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        const file = new File([blob], isWhitelisted ? "whitelisted_demo.jpg" : "unconsented_demo.jpg", {
          type: "image/jpeg",
        });
        resolve(file);
      }, "image/jpeg");
    });
  }

  btnSampleValid.addEventListener("click", async () => {
    const file = await createSampleCanvasImage("HH GOA TEST PHOTO", true);
    await handleSelectedFile(file);
    // Auto whitelist sample
    const hash = await computeSHA256(file);
    if (!whitelistedHashes.includes(hash)) {
      await fetch("/api/consent/whitelist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_hash: hash }),
      });
      fetchWhitelist();
    }
  });

  btnSampleInvalid.addEventListener("click", async () => {
    const file = await createSampleCanvasImage("UNCONSENTED TEST PHOTO", false);
    await handleSelectedFile(file);
    const hash = await computeSHA256(file);
    // Make sure it is NOT in whitelist
    if (whitelistedHashes.includes(hash)) {
      await deleteWhitelistHash(hash);
    }
  });

  // =========================================================================
  // Stepper Controller
  // =========================================================================
  function resetStepper() {
    for (let i = 0; i <= 4; i++) {
      stepCards[i].className = "step-card";
      stepBadges[i].className = "step-badge";
      stepBadges[i].textContent = "WAITING";
      stepDetails[i].className = "step-detail";
      stepDetails[i].innerHTML = "";
    }
  }

  function setStepState(stepIdx, state, badgeText, detailHtml = "") {
    const card = stepCards[stepIdx];
    const badge = stepBadges[stepIdx];
    const detail = stepDetails[stepIdx];

    card.className = `step-card ${state}`;
    badge.className = `step-badge ${state}`;
    badge.textContent = badgeText;
    if (detailHtml) {
      detail.innerHTML = detailHtml;
      detail.classList.add("show");
    }
  }

  function drawFaceBbox(bbox) {
    if (!bbox) return;
    const ctx = faceCanvas.getContext("2d");
    const { x, y, w, h } = bbox;

    ctx.strokeStyle = "#ff3b81";
    ctx.lineWidth = 4;
    ctx.strokeRect(x, y, w, h);

    // Corner Accents
    ctx.fillStyle = "#f5c518";
    const cSize = 8;
    ctx.fillRect(x - 2, y - 2, cSize, cSize);
    ctx.fillRect(x + w - cSize + 2, y - 2, cSize, cSize);
    ctx.fillRect(x - 2, y + h - cSize + 2, cSize, cSize);
    ctx.fillRect(x + w - cSize + 2, y + h - cSize + 2, cSize, cSize);

    // Tag
    ctx.fillStyle = "#ff3b81";
    ctx.fillRect(x, Math.max(0, y - 22), 120, 20);
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.fillText("FACE DETECTED", x + 6, Math.max(14, y - 8));
  }

  // =========================================================================
  // Run Pipeline (Stages 0 - 4)
  // =========================================================================
  btnRunPipeline.addEventListener("click", async () => {
    if (!currentFile || isRunning) return;
    isRunning = true;
    btnRunPipeline.disabled = true;
    uploadSuccessCallout.style.display = "none";
    resetStepper();

    scanLine.style.display = "block";
    log("----------------------------------------", "info");
    log("Initiating pipeline execution (Stages 0–4)...", "info");

    const customSocialUrlInput = document.getElementById("customSocialUrlInput");

    const formData = new FormData();
    formData.append("file", currentFile);
    formData.append("auto_whitelist", autoWhitelistCheck.checked);
    if (customSocialUrlInput && customSocialUrlInput.value.trim()) {
      formData.append("custom_social_url", customSocialUrlInput.value.trim());
    }

    try {
      // Animate Stage 0
      setStepState(0, "active", "VERIFYING CONSENT");

      const response = await fetch("/api/pipeline/run", {
        method: "POST",
        body: formData,
      });

      const resData = await response.json();

      // Log server messages to terminal
      if (resData.logs) {
        resData.logs.forEach((l) => {
          log(`[STAGE ${l.stage}] ${l.message}`, l.status);
        });
      }

      if (!response.ok) {
        // Handled failure (e.g., Consent gate blocked or Face detection failed)
        if (resData.stage === 0) {
          setStepState(
            0,
            "failed",
            "BLOCKED · 403",
            `<span style="color:var(--status-fail);">CONSENT GATE REJECTION: File SHA-256 is not on the whitelist. Execution halted before biometric processing.</span>`
          );
        } else if (resData.stage === 1) {
          setStepState(1, "failed", "DETECTION FAILED", resData.message);
        }
        log(`Pipeline stopped: ${resData.message || "Error"}`, "fail");
        scanLine.style.display = "none";
        isRunning = false;
        btnRunPipeline.disabled = false;
        return;
      }

      // Stage 0 Success
      setStepState(
        0,
        "success",
        "CONSENT PASS",
        `SHA-256 Digest: <code>${resData.file_hash}</code>`
      );

      // Stage 1 Success
      const face = resData.face_meta;
      setStepState(
        1,
        "success",
        "ENCODED",
        `Embedding Vector: ${face.dimensions}-dim · Fingerprint: <code>${resData.emb_hash.slice(0, 24)}…</code><br><span style="color:var(--status-pass);">✓ Strict In-Memory Guarantee: 0 bytes written to disk.</span>`
      );
      drawFaceBbox(face.bbox);

      // Stage 2
      if (!resData.match_found) {
        setStepState(
          2,
          "active",
          "HONEST NO-MATCH",
          `Checked social domains: <code>instagram.com, x.com, linkedin.com, facebook.com</code>.<br><span style="color:var(--text-pink);">Zero fabricated matches per PRD specification.</span>`
        );
        log("Pipeline terminated honestly: No social match found.", "warn");
        scanLine.style.display = "none";
        isRunning = false;
        btnRunPipeline.disabled = false;
        return;
      }

      let accountsHtml = "";
      if (resData.discovered_accounts && resData.discovered_accounts.length > 0) {
        accountsHtml = '<div style="margin-top:8px;display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:6px;">' +
          resData.discovered_accounts.map(acc => 
            `<a href="${acc.url}" target="_blank" style="text-decoration:none;background:var(--brand-green);color:var(--color-white);padding:6px 10px;border-radius:var(--radius-sm);font-size:11px;font-weight:700;border:1px solid var(--brand-pink);display:flex;align-items:center;justify-content:space-between;gap:6px;transition:all 0.2s ease;">
              <span style="display:flex;align-items:center;gap:4px;"><span style="color:var(--brand-pink);">✦</span> ${acc.platform}</span>
              <span style="font-size:10px;opacity:0.85;text-overflow:ellipsis;overflow:hidden;white-space:nowrap;max-width:110px;">${acc.url.replace(/^https?:\/\/(www\.)?/, '')} ↗</span>
            </a>`
          ).join("") + '</div>';
      }

      setStepState(
        2,
        "success",
        `${resData.discovered_accounts ? resData.discovered_accounts.length : 1} ACCOUNTS IDENTIFIED`,
        `<b>Primary Verified Profile:</b> <a href="${resData.match.url}" target="_blank" style="color:var(--brand-pink);font-weight:bold;">${resData.match.url}</a><br>
        <span style="font-size:11.5px;color:var(--brand-green);font-weight:800;display:block;margin-top:6px;">Identified Active Accounts for Person:</span>
        ${accountsHtml}`
      );

      // Stage 3
      setStepState(
        3,
        "success",
        "RETRIEVED",
        `Content SHA-256: <code>${resData.content_hash}</code>`
      );

      // Stage 4
      const blk = resData.block;
      setStepState(
        4,
        "success",
        `BLOCK #${blk.index} MINTED`,
        `Block Hash: <code>${blk.block_hash.slice(0, 28)}…</code><br>Prev Hash: <code>${blk.previous_hash.slice(0, 28)}…</code>`
      );

      latestMintedUrl = resData.match ? resData.match.url : "";
      if (latestMintedUrl) {
        verifyUrlInput.value = latestMintedUrl;
      }

      uploadSuccessCallout.style.display = "block";
      fetchBlockchain();
      log("✓ Pipeline Stages 0–4 successfully executed and recorded.", "ok");
    } catch (e) {
      log(`Pipeline execution error: ${e.message}`, "fail");
    } finally {
      scanLine.style.display = "none";
      isRunning = false;
      btnRunPipeline.disabled = false;
    }
  });

  // =========================================================================
  // Independent Verifier (Stage 5)
  // =========================================================================
  btnTriggerVerify.addEventListener("click", async () => {
    const url = verifyUrlInput.value.trim();
    btnTriggerVerify.disabled = true;
    verifyResultBox.style.display = "none";

    log("----------------------------------------", "info");
    log(`[STAGE 5] Starting independent verification process...`, "info");

    try {
      const res = await fetch("/api/pipeline/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url || null }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Verification request failed");

      // Render Verdict
      const isPass = data.verified;
      verdictBanner.className = `verdict-banner ${isPass ? "" : "fail"}`;
      verdictIcon.textContent = isPass ? "✓" : "✗";
      verdictTitle.textContent = isPass ? "VERIFICATION PASS" : "VERIFICATION FAIL";
      verdictSub.textContent = isPass
        ? "Re-computed hash matches the on-chain record and full chain cryptographic integrity is verified."
        : "Cryptographic tamper detected! Content hash mismatch or broken blockchain links.";

      // Render Table
      auditTableBody.innerHTML = "";
      data.checks.forEach((chk) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><b>${chk.name}</b></td>
          <td><code>${chk.detail}</code></td>
          <td class="text-center">
            <span class="verdict-pill ${chk.status.toLowerCase()}">${chk.status}</span>
          </td>
        `;
        auditTableBody.appendChild(tr);
      });

      storedHashVal.textContent = data.stored_hash;
      recomputedHashVal.textContent = data.recomputed_hash;
      verifyResultBox.style.display = "block";

      log(`[STAGE 5] Audit result: ${data.verdict} (Integrity: ${data.chain_integrity}, Match: ${data.hash_match})`, isPass ? "ok" : "fail");
    } catch (e) {
      alert(`Verification error: ${e.message}`);
      log(`[STAGE 5] Error: ${e.message}`, "fail");
    } finally {
      btnTriggerVerify.disabled = false;
    }
  });

  // =========================================================================
  // Blockchain Ledger Explorer
  // =========================================================================
  async function fetchBlockchain() {
    try {
      const res = await fetch("/api/blockchain");
      const data = await res.json();
      const blocks = data.blocks || [];
      chainCountBadge.textContent = blocks.length;

      // Integrity Pill
      if (data.integrity_valid) {
        chainIntegrityPill.className = "chain-status-pill";
        chainIntegrityPill.textContent = "INTEGRITY: VALID";
      } else {
        chainIntegrityPill.className = "chain-status-pill invalid";
        chainIntegrityPill.textContent = "INTEGRITY: TAMPERED / INVALID";
      }

      renderBlockchainRibbon(blocks);
      populateTamperSelect(blocks);
    } catch (e) {
      log(`Explorer error: ${e.message}`, "fail");
    }
  }

  function renderBlockchainRibbon(blocks) {
    if (!blocks.length) {
      blockchainRibbon.innerHTML = '<div class="empty-chain-placeholder">No blocks recorded yet. Run upload stage to mint Block #0.</div>';
      blockInspector.style.display = "none";
      return;
    }

    blockchainRibbon.innerHTML = "";
    blocks.forEach((b, idx) => {
      const card = document.createElement("div");
      card.className = "block-card";
      card.innerHTML = `
        <div class="block-card-header">
          <span class="block-idx-tag">BLOCK #${b.index}</span>
          <span class="block-timestamp">${new Date(b.timestamp).toLocaleTimeString()}</span>
        </div>
        <div class="block-row">
          <span class="block-lbl">DATA HASH</span>
          <span class="block-val">${b.data_hash.slice(0, 16)}…</span>
        </div>
        <div class="block-row">
          <span class="block-lbl">PREV HASH</span>
          <span class="block-val">${b.previous_hash.slice(0, 16)}…</span>
        </div>
        <div class="block-row">
          <span class="block-lbl">URL</span>
          <span class="block-val" style="color:var(--brand-pink);">${b.metadata.url || "N/A"}</span>
        </div>
      `;
      card.addEventListener("click", () => inspectBlock(b));
      blockchainRibbon.appendChild(card);

      if (idx < blocks.length - 1) {
        const conn = document.createElement("div");
        conn.className = "block-connector";
        conn.textContent = "→";
        blockchainRibbon.appendChild(conn);
      }
    });

    // Default inspect latest
    inspectBlock(blocks[blocks.length - 1]);
  }

  function inspectBlock(block) {
    inspectorHeader.textContent = `Block #${block.index} Inspection · Raw Cryptographic Record`;
    inspectorJson.textContent = JSON.stringify(block, null, 2);
    blockInspector.style.display = "block";
  }

  btnResetChain.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to reset the simulated blockchain?")) return;
    try {
      await fetch("/api/blockchain/reset", { method: "POST" });
      log("Blockchain reset.", "warn");
      fetchBlockchain();
    } catch (e) {
      log(`Reset failed: ${e.message}`, "fail");
    }
  });

  // =========================================================================
  // Tamper Sandbox
  // =========================================================================
  async function populateTamperSelect(blocks) {
    if (!blocks) {
      const res = await fetch("/api/blockchain");
      const data = await res.json();
      blocks = data.blocks || [];
    }

    tamperBlockSelect.innerHTML = '<option value="">-- Select a block --</option>';
    blocks.forEach((b) => {
      const opt = document.createElement("option");
      opt.value = b.index;
      opt.textContent = `Block #${b.index} (${b.metadata.url || "URL"}) - Current Hash: ${b.data_hash.slice(0, 12)}…`;
      tamperBlockSelect.appendChild(opt);
    });
  }

  btnInjectTamper.addEventListener("click", async () => {
    const idx = tamperBlockSelect.value;
    if (idx === "") {
      alert("Please select a block to tamper.");
      return;
    }
    const val = tamperNewData.value.trim();
    try {
      const res = await fetch("/api/blockchain/tamper", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ block_index: parseInt(idx), new_data: val }),
      });
      const data = await res.json();
      tamperStatusLog.innerHTML = `
        <span style="color:var(--status-fail);font-weight:bold;">⚠️ TAMPER INJECTED:</span><br>
        Block #${idx} data_hash was modified on disk.<br>
        Chain Integrity Valid: <b>${data.integrity_now_valid}</b>
      `;
      btnVerifyTamper.disabled = false;
      log(`⚠️ Tampered block #${idx} with counterfeit data hash.`, "fail");
      fetchBlockchain();
    } catch (e) {
      log(`Tamper error: ${e.message}`, "fail");
    }
  });

  btnVerifyTamper.addEventListener("click", () => {
    document.querySelector('[data-tab="verifier"]').click();
    btnTriggerVerify.click();
  });

  // =========================================================================
  // Initialization
  // =========================================================================
  fetchWhitelist();
  fetchBlockchain();
  log("HH Goa 2026 Verification System Initialized.", "ok");
});
