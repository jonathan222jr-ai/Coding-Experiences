/* global Office, document */

import { scanEmail } from "../scanner";
import type { EmailModel } from "../scanner";
import { BACKEND_URL } from "../config";

Office.onReady(() => {
  const button = document.getElementById("scan-email");
  const rescanBtn = document.getElementById("rescan-btn");
  loadLocalStats();

  if (button) {
    button.addEventListener("click", runScan);
  } else {
    console.error('Button with id "scan-email" not found.');
  }
  if (rescanBtn) {
    rescanBtn.addEventListener("click", resetScanner);
  }
  function loadLocalStats() {
    const scanned = Number(localStorage.getItem("sweep_scanned") || "0");
    const fraud = Number(localStorage.getItem("sweep_fraud") || "0");

    const scannedEl = document.getElementById("emails-scanned");
    const fraudEl = document.getElementById("fraud-detected");

    if (scannedEl) scannedEl.textContent = `${scanned.toLocaleString()} emails scanned`;
    if (fraudEl) fraudEl.textContent = `${fraud.toLocaleString()} fraud detected`;
  }
});

async function runScan() {
   const scanBtn = document.getElementById("scan-email") as HTMLButtonElement;

  if (scanBtn) {
    scanBtn.disabled = true;
    scanBtn.innerHTML = '<span class="scan-btn__text">Scanning...</span>';
  }

  const item = Office.context.mailbox.item as any;

  if (!item) {
    console.error("No Outlook item is open.");
    return;
  }

  try {
    const subject = item.subject || "";
    const body = await getBodyText(item);
    const sender = getSenderEmail(item);
    const senderDisplayName = getSenderDisplayName(item);
    const attachments = getAttachmentNames(item);
    const links = extractLinks(body);

    const email: EmailModel = {
      subject,
      sender,
      senderDisplayName,
      body,
      links,
      attachments,
    };

    const result = scanEmail(email);

    let backendResult: any = null;

    try {
      backendResult = await callBackend(email, result);
    } catch (backendError) {
      console.error("Backend/Ollama scan failed:", backendError);
    }

    const merged = mergeScanResults(result, backendResult);

    updateRiskUI({
      riskLevel: merged.riskLevel,
      riskScore: merged.riskScore,
      flags: merged.flags,
      linksFound: result.feature_summary.num_links,
      suspiciousSender: result.feature_summary.spoofed_domain,
      credentialRequest: result.feature_summary.credential_request,
      suspiciousAttachment: result.feature_summary.suspicious_attachment,
    });

    updateScanChart(merged.riskScore);
    updateLocalStats(merged.riskScore);
    renderLlmSummary(backendResult);
    document.getElementById("scan-actions")?.classList.remove("hidden");
  } catch (error) {
    console.error("Scan failed:", error);
  }
  finally {
    const scanBtn = document.getElementById("scan-email") as HTMLButtonElement;
    if (scanBtn) {
      scanBtn.disabled = false;
      scanBtn.innerHTML = '<span class="scan-btn__text">Scan<br>Email</span>';
    }
  }
}

function getBodyText(item: any): Promise<string> {
  return new Promise((resolve, reject) => {
    item.body.getAsync(Office.CoercionType.Text, (result: any) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        resolve(result.value || "");
      } else {
        reject(result.error);
      }
    });
  });
}

function getSenderEmail(item: any): string {
  return item.from?.emailAddress || item.sender?.emailAddress || "";
}

function getSenderDisplayName(item: any): string {
  return item.from?.displayName || item.sender?.displayName || "";
}

function getAttachmentNames(item: any): string[] {
  if (!item.attachments) return [];
  return item.attachments.map((a: any) => a.name).filter(Boolean);
}

function extractLinks(text: string): string[] {
  return text.match(/https?:\/\/[^\s]+/gi) || [];
}

async function callBackend(email: EmailModel, localScan: any) {
  const response = await fetch(BACKEND_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      local_scan: localScan,
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend request failed with status ${response.status}`);
  }

  return response.json();
}

function mergeScanResults(localResult: any, backendResult: any) {
  const localFlags = Array.isArray(localResult?.flags)
    ? localResult.flags.map((flag: any) => {
        if (typeof flag === "string") return flag;
        if (flag?.name) return flag.name;
        return String(flag);
      })
    : [];

  const llmFlags = Array.isArray(backendResult?.llm_scan?.red_flags)
    ? backendResult.llm_scan.red_flags
    : [];

  const combinedFlags = [...new Set([...localFlags, ...llmFlags])];

  const finalScore =
    typeof backendResult?.final?.score === "number"
      ? backendResult.final.score
      : localResult.risk_score;

  const finalVerdict =
    typeof backendResult?.final?.verdict === "string"
      ? backendResult.final.verdict
      : localResult.risk_level;

  return {
    riskLevel: normalizeRiskLevel(finalVerdict, finalScore),
    riskScore: Math.max(0, Math.min(finalScore, 100)),
    flags: combinedFlags,
  };
}

function normalizeRiskLevel(verdict: string, score: number): string {
  const upper = (verdict || "").toUpperCase();

  if (upper.includes("HIGH") || upper.includes("PHISH")) return "HIGH";
  if (upper.includes("MED")) return "MED";
  if (upper.includes("LOW") || upper.includes("SAFE")) return "LOW";

  if (score >= 70) return "HIGH";
  if (score >= 40) return "MED";
  return "LOW";
}

function updateScanChart(riskScore: number) {
  const button = document.getElementById("scan-email");
  const chart = document.getElementById("scan-chart");
  const pie = document.getElementById("scan-chart-pie");
  const safePercentText = document.getElementById("scan-safe-percent");

  const safePercent = Math.max(0, Math.min(100, 100 - riskScore));

  if (button) {
    button.classList.add("hidden");
  }

  if (chart) {
    chart.classList.remove("hidden");
  }

  if (pie) {
    pie.setAttribute(
      "style",
      `background: conic-gradient(#22c55e 0% ${safePercent}%, #ef4444 ${safePercent}% 100%);`
    );
  }

  if (safePercentText) {
    safePercentText.textContent = `${safePercent}%`;
  }
}

function updateRiskUI(result: {
  riskLevel: string;
  riskScore: number;
  flags: string[];
  linksFound: number;
  suspiciousSender: boolean;
  credentialRequest: boolean;
  suspiciousAttachment: boolean;
}) {
  const badge = document.getElementById("risk-badge");
  const meterFill = document.getElementById("risk-meter-fill");
  const score = document.getElementById("risk-score");
  const flags = document.getElementById("risk-flags");
  const links = document.getElementById("risk-links");
  const sender = document.getElementById("risk-sender");
  const credential = document.getElementById("risk-credential");
  const attachment = document.getElementById("risk-attachment");

  if (badge) badge.textContent = result.riskLevel;
  if (meterFill) meterFill.style.width = `${Math.max(0, Math.min(result.riskScore, 100))}%`;
  if (score) score.textContent = String(result.riskScore);
  if (flags) flags.textContent = result.flags.length ? result.flags.join(", ") : "None";
  if (links) links.textContent = String(result.linksFound);

  if (sender) {
    sender.textContent = result.suspiciousSender ? "Yes" : "No";
  }

  if (credential) {
    credential.textContent = result.credentialRequest ? "Yes" : "No";
  }

  if (attachment) {
    attachment.textContent = result.suspiciousAttachment ? "Yes" : "No";
  }

  if (badge) {
    badge.className = "risk-card__badge";

    if (result.riskScore >= 70) {
      badge.textContent = "HIGH";
      badge.style.background = "#fee2e2";
      badge.style.color = "#b91c1c";
      if (meterFill) meterFill.style.background = "linear-gradient(90deg, #ef4444, #dc2626)";
    } else if (result.riskScore >= 40) {
      badge.textContent = "MED";
      badge.style.background = "#fef3c7";
      badge.style.color = "#b45309";
      if (meterFill) meterFill.style.background = "linear-gradient(90deg, #f59e0b, #eab308)";
    } else {
      badge.textContent = "LOW";
      badge.style.background = "#dcfce7";
      badge.style.color = "#15803d";
      if (meterFill) meterFill.style.background = "linear-gradient(90deg, #22c55e, #84cc16)";
    }
  }
}

function updateLocalStats(riskScore: number) {
  let scanned = Number(localStorage.getItem("sweep_scanned") || "0");
  let fraud = Number(localStorage.getItem("sweep_fraud") || "0");

  scanned += 1;

  if (riskScore >= 50) {
    fraud += 1;
  }

  localStorage.setItem("sweep_scanned", scanned.toString());
  localStorage.setItem("sweep_fraud", fraud.toString());

  const scannedEl = document.getElementById("emails-scanned");
  const fraudEl = document.getElementById("fraud-detected");

  if (scannedEl) scannedEl.textContent = `${scanned.toLocaleString()} emails scanned`;
  if (fraudEl) fraudEl.textContent = `${fraud.toLocaleString()} fraud detected`;
}

function renderLlmSummary(backendResult: any) {
  const riskCard = document.getElementById("risk-card");
  if (!riskCard) return;

  let llmBox = document.getElementById("llm-summary-box");

  if (!llmBox) {
    llmBox = document.createElement("div");
    llmBox.id = "llm-summary-box";
    llmBox.style.marginTop = "12px";
    llmBox.style.paddingTop = "10px";
    llmBox.style.borderTop = "1px solid #e5e7eb";
    riskCard.appendChild(llmBox);
  }

  if (!backendResult?.llm_scan && !backendResult?.final) {
    llmBox.innerHTML = `
      <div style="font-size:12px; font-weight:700; color:#6b7280; text-transform:uppercase; margin-bottom:6px;">
        Ollama Deep Scan
      </div>
      <div style="font-size:12px; color:#6b7280;">
        Backend unavailable.
      </div>
    `;
    return;
  }

  const verdict = backendResult?.llm_scan?.verdict ?? "N/A";
  const score = backendResult?.llm_scan?.score ?? "N/A";
  const summary = backendResult?.final?.summary ?? "No summary provided.";
  const reasons = Array.isArray(backendResult?.llm_scan?.reasons)
    ? backendResult.llm_scan.reasons.slice(0, 3)
    : [];

  llmBox.innerHTML = `
    <div style="font-size:12px; font-weight:700; color:#6b7280; text-transform:uppercase; margin-bottom:6px;">
      Ollama Deep Scan
    </div>
    <div style="font-size:13px; color:#111827; margin-bottom:4px;">
      <strong>Verdict:</strong> ${escapeHtml(String(verdict))}
    </div>
    <div style="font-size:13px; color:#111827; margin-bottom:6px;">
      <strong>LLM Score:</strong> ${escapeHtml(String(score))}
    </div>
    <div style="font-size:12px; color:#374151; margin-bottom:6px;">
      ${escapeHtml(String(summary))}
    </div>
    ${
      reasons.length
        ? `<ul style="margin:6px 0 0 18px; padding:0; color:#374151; font-size:12px;">
            ${reasons.map((reason: string) => `<li>${escapeHtml(reason)}</li>`).join("")}
          </ul>`
        : ""
    }
  `;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function resetScanner() {
  const button = document.getElementById("scan-email");
  const chart = document.getElementById("scan-chart");
  const actions = document.getElementById("scan-actions");
  const pie = document.getElementById("scan-chart-pie");
  const safePercentText = document.getElementById("scan-safe-percent");

  const badge = document.getElementById("risk-badge");
  const meterFill = document.getElementById("risk-meter-fill");
  const score = document.getElementById("risk-score");
  const flags = document.getElementById("risk-flags");
  const links = document.getElementById("risk-links");
  const sender = document.getElementById("risk-sender");
  const credential = document.getElementById("risk-credential");
  const attachment = document.getElementById("risk-attachment");
  const llmBox = document.getElementById("llm-summary-box");

  if (button) button.classList.remove("hidden");
  if (chart) chart.classList.add("hidden");
  if (actions) actions.classList.add("hidden");

  if (pie) {
    pie.setAttribute(
      "style",
      "background: conic-gradient(#22c55e 0% 80%, #ef4444 80% 100%);"
    );
  }

  if (safePercentText) safePercentText.textContent = "80%";

  if (badge) {
    badge.textContent = "LOW";
    badge.className = "risk-card__badge";
    (badge as HTMLElement).style.background = "#dcfce7";
    (badge as HTMLElement).style.color = "#15803d";
  }

  if (meterFill) {
    (meterFill as HTMLElement).style.width = "0%";
    (meterFill as HTMLElement).style.background = "linear-gradient(90deg, #22c55e, #84cc16)";
  }

  if (score) score.textContent = "0";
  if (flags) flags.textContent = "None";
  if (links) links.textContent = "0";
  if (sender) sender.textContent = "No";
  if (credential) credential.textContent = "No";
  if (attachment) attachment.textContent = "No";
  if (llmBox) llmBox.remove();
}