/* global Office, document, localStorage, fetch */

import { scanEmail, type EmailModel, type Flag, type ScanResult } from "../scanner";

type BackendResponse = {
  llm_scan?: {
    verdict?: string;
    score?: number;
    reasons?: string[];
    red_flags?: string[];
  };
  final?: {
    verdict?: string;
    score?: number;
    summary?: string;
  };
};

type UiScanResult = {
  riskLevel: "SAFE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  riskScore: number;
  flags: string[];
  linksFound: number;
  suspiciousSender: boolean;
  credentialRequest: boolean;
  suspiciousAttachment: boolean;
};

const STATS_SCANNED_KEY = "sweep_scanned";
const STATS_FRAUD_KEY = "sweep_fraud";

Office.onReady(() => {
  bindUi();
  loadLocalStats();
  resetScanner();
});

function bindUi(): void {
  const scanButton = document.getElementById("scan-email");
  const rescanButton = document.getElementById("rescan-btn");

  scanButton?.addEventListener("click", () => {
    void runScan();
  });

  rescanButton?.addEventListener("click", resetScanner);
}

async function runScan(): Promise<void> {
  const scanButton = document.getElementById("scan-email") as HTMLButtonElement | null;
  setScanButtonLoading(scanButton, true);

  try {
    const item = Office.context.mailbox?.item as any;
    if (!item) {
      throw new Error("No Outlook email is open in the reading pane.");
    }

    const email = await buildEmailModel(item);
    const localScan = scanEmail(email);

    let backendResult: BackendResponse | null = null;
    if (shouldAttemptBackend(localScan)) {
      try {
        backendResult = await callBackend(email, localScan);
      } catch (error) {
        console.error("Deep scan backend unavailable:", error);
      }
    }

    const mergedResult = mergeScanResults(localScan, backendResult);

    updateRiskUI({
      riskLevel: mergedResult.riskLevel,
      riskScore: mergedResult.riskScore,
      flags: mergedResult.flags,
      linksFound: localScan.feature_summary.num_links,
      suspiciousSender: localScan.feature_summary.spoofed_domain,
      credentialRequest: localScan.feature_summary.credential_request,
      suspiciousAttachment: localScan.feature_summary.suspicious_attachment,
    });

    updateScanChart(mergedResult.riskScore);
    updateLocalStats(mergedResult.riskScore);
    renderLlmSummary(localScan, backendResult);

    document.getElementById("scan-actions")?.classList.remove("hidden");
  } catch (error) {
    console.error("Scan failed:", error);
    renderError(error instanceof Error ? error.message : "Unable to scan this email.");
  } finally {
    setScanButtonLoading(scanButton, false);
  }
}

async function buildEmailModel(item: any): Promise<EmailModel> {
  const [bodyText, bodyHtml, headers] = await Promise.all([
    getBodyAsync(item, Office.CoercionType.Text),
    getBodyAsync(item, Office.CoercionType.Html),
    getInternetHeadersAsync(item),
  ]);

  const senderEmail = getSenderEmail(item);
  const senderDisplayName = getSenderDisplayName(item);
  const attachments = getAttachmentNames(item);
  const links = Array.from(new Set([...extractLinksFromHtml(bodyHtml), ...extractLinksFromText(bodyText)]));

  return {
    subject: item.subject || "",
    sender: senderEmail,
    senderDisplayName,
    senderName: senderDisplayName,
    replyTo: getReplyToAddress(item),
    recipient: getPrimaryRecipient(item),
    cc: getCcRecipients(item),
    body: bodyText,
    bodyHtml,
    links,
    attachments,
    embeddedText: bodyText,
    headers,
    auth: parseAuthSignals(headers),
    config: getScannerConfig(),
  };
}

function getScannerConfig() {
  return {
    trustedDomains: readCsvList("sweep_trusted_domains"),
    safeSenderDomains: readCsvList("sweep_safe_sender_domains"),
    sensitivity: 1,
    sendLowRiskToLLM: false,
    llmEscalationThreshold: "MEDIUM" as const,
  };
}

function readCsvList(storageKey: string): string[] {
  const value = localStorage.getItem(storageKey) || "";
  return value
    .split(",")
    .map((entry) => entry.trim().toLowerCase())
    .filter(Boolean);
}

function getBodyAsync(item: any, coercionType: Office.CoercionType): Promise<string> {
  return new Promise((resolve, reject) => {
    item.body.getAsync(coercionType, (result: Office.AsyncResult<string>) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        resolve(result.value || "");
      } else {
        reject(result.error || new Error("Failed to read email body."));
      }
    });
  });
}

function getInternetHeadersAsync(item: any): Promise<Record<string, string>> {
  return new Promise((resolve) => {
    if (typeof item.getAllInternetHeadersAsync !== "function") {
      resolve({});
      return;
    }

    item.getAllInternetHeadersAsync((result: Office.AsyncResult<string>) => {
      if (result.status !== Office.AsyncResultStatus.Succeeded || !result.value) {
        resolve({});
        return;
      }

      resolve(parseRawHeaders(result.value));
    });
  });
}

function parseRawHeaders(rawHeaders: string): Record<string, string> {
  const headers: Record<string, string> = {};
  const lines = rawHeaders.split(/\r?\n/);

  let currentKey = "";
  for (const line of lines) {
    if (!line.trim()) continue;

    if (/^\s/.test(line) && currentKey) {
      headers[currentKey] = `${headers[currentKey]} ${line.trim()}`.trim();
      continue;
    }

    const separator = line.indexOf(":");
    if (separator === -1) continue;

    currentKey = line.slice(0, separator).trim();
    headers[currentKey] = line.slice(separator + 1).trim();
  }

  return headers;
}

function parseAuthSignals(headers: Record<string, string>): EmailModel["auth"] {
  const authResults =
    headers["Authentication-Results"] ||
    headers["authentication-results"] ||
    "";

  const lower = authResults.toLowerCase();

  return {
    spf: /\bspf=pass\b/.test(lower)
      ? "pass"
      : /\bspf=softfail\b/.test(lower)
        ? "softfail"
        : /\bspf=fail\b/.test(lower)
          ? "fail"
          : /\bspf=neutral\b/.test(lower)
            ? "neutral"
            : "none",
    dkim: /\bdkim=pass\b/.test(lower)
      ? "pass"
      : /\bdkim=fail\b/.test(lower)
        ? "fail"
        : "none",
    dmarc: /\bdmarc=pass\b/.test(lower)
      ? "pass"
      : /\bdmarc=fail\b/.test(lower)
        ? "fail"
        : "none",
  };
}

function getSenderEmail(item: any): string {
  return item.from?.emailAddress || item.sender?.emailAddress || "";
}

function getSenderDisplayName(item: any): string {
  return item.from?.displayName || item.sender?.displayName || "";
}

function getReplyToAddress(item: any): string | undefined {
  const replyTo = item.replyTo;
  if (Array.isArray(replyTo) && replyTo.length > 0) {
    return replyTo[0]?.emailAddress || undefined;
  }
  return undefined;
}

function getPrimaryRecipient(item: any): string | undefined {
  const recipient = Array.isArray(item.to) && item.to.length > 0 ? item.to[0] : null;
  return recipient?.emailAddress || undefined;
}

function getCcRecipients(item: any): string[] {
  return Array.isArray(item.cc)
    ? item.cc.map((entry: any) => entry?.emailAddress).filter(Boolean)
    : [];
}

function getAttachmentNames(item: any): string[] {
  return Array.isArray(item.attachments)
    ? item.attachments.map((attachment: any) => attachment?.name).filter(Boolean)
    : [];
}

function extractLinksFromText(text: string): string[] {
  return text.match(/https?:\/\/[^\s<>")]+/gi) || [];
}

function extractLinksFromHtml(html: string): string[] {
  if (!html) return [];

  const links = [...html.matchAll(/href\s*=\s*["']([^"'#]+)["']/gi)]
    .map((match) => match[1])
    .filter(Boolean);

  return links;
}

function shouldAttemptBackend(localScan: ScanResult): boolean {
  const backendUrl = getBackendUrl();
  if (!backendUrl) return false;
  return localScan.llm_escalation.should_escalate;
}

function getBackendUrl(): string {
  const globalUrl = (globalThis as any)?.BACKEND_URL;
  if (typeof globalUrl === "string" && globalUrl.trim()) {
    return globalUrl.trim();
  }

  const storageUrl = localStorage.getItem("sweep_backend_url");
  if (storageUrl && storageUrl.trim()) {
    return storageUrl.trim();
  }

  return "";
}

async function callBackend(email: EmailModel, localScan: ScanResult): Promise<BackendResponse> {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    throw new Error("No backend URL configured.");
  }

  const response = await fetch(backendUrl, {
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

  return (await response.json()) as BackendResponse;
}

function mergeScanResults(localResult: ScanResult, backendResult: BackendResponse | null): UiScanResult {
  const localFlags = localResult.flags.map((flag: Flag) => String(flag));
  const backendFlags = Array.isArray(backendResult?.llm_scan?.red_flags)
    ? backendResult!.llm_scan!.red_flags!.map((flag) => String(flag))
    : [];

  const riskScore = clampScore(
    typeof backendResult?.final?.score === "number"
      ? backendResult.final.score
      : localResult.risk_score
  );

  const riskLevel = normalizeRiskLevel(
    typeof backendResult?.final?.verdict === "string"
      ? backendResult.final.verdict
      : localResult.risk_level,
    riskScore
  );

  return {
    riskLevel,
    riskScore,
    flags: Array.from(new Set([...localFlags, ...backendFlags])),
    linksFound: localResult.feature_summary.num_links,
    suspiciousSender: localResult.feature_summary.spoofed_domain,
    credentialRequest: localResult.feature_summary.credential_request,
    suspiciousAttachment: localResult.feature_summary.suspicious_attachment,
  };
}

function normalizeRiskLevel(verdict: string, score: number): UiScanResult["riskLevel"] {
  const upper = String(verdict || "").toUpperCase();

  if (upper.includes("CRITICAL")) return "CRITICAL";
  if (upper.includes("HIGH") || upper.includes("PHISH")) return "HIGH";
  if (upper.includes("MED")) return "MEDIUM";
  if (upper.includes("LOW")) return "LOW";
  if (upper.includes("SAFE")) return "SAFE";

  if (score >= 85) return "CRITICAL";
  if (score >= 65) return "HIGH";
  if (score >= 35) return "MEDIUM";
  if (score >= 15) return "LOW";
  return "SAFE";
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function setScanButtonLoading(button: HTMLButtonElement | null, loading: boolean): void {
  if (!button) return;

  button.disabled = loading;
  button.innerHTML = loading
    ? '<span class="scan-btn__text">Scanning...</span>'
    : '<span class="scan-btn__text">Scan<br>Email</span>';
}

function updateScanChart(riskScore: number): void {
  const button = document.getElementById("scan-email");
  const chart = document.getElementById("scan-chart");
  const pie = document.getElementById("scan-chart-pie") as HTMLElement | null;
  const safePercentText = document.getElementById("scan-safe-percent");

  const safePercent = clampScore(100 - riskScore);

  button?.classList.add("hidden");
  chart?.classList.remove("hidden");

  if (pie) {
    pie.style.background = `conic-gradient(#22c55e 0% ${safePercent}%, #ef4444 ${safePercent}% 100%)`;
  }

  if (safePercentText) {
    safePercentText.textContent = `${safePercent}%`;
  }
}

function updateRiskUI(result: UiScanResult): void {
  const badge = document.getElementById("risk-badge") as HTMLElement | null;
  const meterFill = document.getElementById("risk-meter-fill") as HTMLElement | null;
  const score = document.getElementById("risk-score");
  const flags = document.getElementById("risk-flags");
  const links = document.getElementById("risk-links");
  const sender = document.getElementById("risk-sender");
  const credential = document.getElementById("risk-credential");
  const attachment = document.getElementById("risk-attachment");

  if (badge) {
    badge.textContent = badgeLabel(result.riskLevel);
    badge.className = "risk-card__badge";

    if (result.riskLevel === "CRITICAL" || result.riskLevel === "HIGH") {
      badge.style.background = "#fee2e2";
      badge.style.color = "#b91c1c";
    } else if (result.riskLevel === "MEDIUM") {
      badge.style.background = "#fef3c7";
      badge.style.color = "#b45309";
    } else {
      badge.style.background = "#dcfce7";
      badge.style.color = "#15803d";
    }
  }

  if (meterFill) {
    meterFill.style.width = `${result.riskScore}%`;
    meterFill.style.background = meterGradient(result.riskLevel);
  }

  if (score) score.textContent = String(result.riskScore);
  if (flags) flags.textContent = result.flags.length > 0 ? result.flags.join(", ") : "None";
  if (links) links.textContent = String(result.linksFound);
  if (sender) sender.textContent = result.suspiciousSender ? "Yes" : "No";
  if (credential) credential.textContent = result.credentialRequest ? "Yes" : "No";
  if (attachment) attachment.textContent = result.suspiciousAttachment ? "Yes" : "No";
}

function badgeLabel(level: UiScanResult["riskLevel"]): string {
  switch (level) {
    case "CRITICAL":
      return "CRITICAL";
    case "HIGH":
      return "HIGH";
    case "MEDIUM":
      return "MED";
    case "LOW":
      return "LOW";
    default:
      return "SAFE";
  }
}

function meterGradient(level: UiScanResult["riskLevel"]): string {
  switch (level) {
    case "CRITICAL":
    case "HIGH":
      return "linear-gradient(90deg, #ef4444, #dc2626)";
    case "MEDIUM":
      return "linear-gradient(90deg, #f59e0b, #eab308)";
    default:
      return "linear-gradient(90deg, #22c55e, #84cc16)";
  }
}

function renderLlmSummary(localScan: ScanResult, backendResult: BackendResponse | null): void {
  const riskCard = document.getElementById("risk-card");
  if (!riskCard) return;

  let summaryBox = document.getElementById("llm-summary-box") as HTMLDivElement | null;
  if (!summaryBox) {
    summaryBox = document.createElement("div");
    summaryBox.id = "llm-summary-box";
    summaryBox.style.marginTop = "12px";
    summaryBox.style.paddingTop = "10px";
    summaryBox.style.borderTop = "1px solid #e5e7eb";
    riskCard.appendChild(summaryBox);
  }

  const localPolicy = localScan.llm_escalation;

  if (!backendResult) {
    summaryBox.innerHTML = `
      <div style="font-size:12px; font-weight:700; color:#6b7280; text-transform:uppercase; margin-bottom:6px;">
        Deep Scan
      </div>
      <div style="font-size:12px; color:#374151; margin-bottom:6px;">
        Escalation: <strong>${localPolicy.should_escalate ? "Yes" : "No"}</strong>
      </div>
      <div style="font-size:12px; color:#6b7280;">
        ${escapeHtml(localPolicy.reason)}
      </div>
    `;
    return;
  }

  const verdict = backendResult.llm_scan?.verdict ?? backendResult.final?.verdict ?? "N/A";
  const score = backendResult.llm_scan?.score ?? backendResult.final?.score ?? "N/A";
  const summary = backendResult.final?.summary ?? "No summary provided.";
  const reasons = Array.isArray(backendResult.llm_scan?.reasons)
    ? backendResult.llm_scan!.reasons!.slice(0, 3)
    : [];

  summaryBox.innerHTML = `
    <div style="font-size:12px; font-weight:700; color:#6b7280; text-transform:uppercase; margin-bottom:6px;">
      Deep Scan
    </div>
    <div style="font-size:13px; color:#111827; margin-bottom:4px;">
      <strong>Verdict:</strong> ${escapeHtml(String(verdict))}
    </div>
    <div style="font-size:13px; color:#111827; margin-bottom:6px;">
      <strong>LLM Score:</strong> ${escapeHtml(String(score))}
    </div>
    <div style="font-size:12px; color:#374151; margin-bottom:6px;">
      ${escapeHtml(summary)}
    </div>
    ${
      reasons.length > 0
        ? `<ul style="margin:6px 0 0 18px; padding:0; color:#374151; font-size:12px;">
            ${reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}
          </ul>`
        : ""
    }
  `;
}

function renderError(message: string): void {
  const riskCard = document.getElementById("risk-card");
  if (!riskCard) return;

  let errorBox = document.getElementById("llm-summary-box") as HTMLDivElement | null;
  if (!errorBox) {
    errorBox = document.createElement("div");
    errorBox.id = "llm-summary-box";
    errorBox.style.marginTop = "12px";
    errorBox.style.paddingTop = "10px";
    errorBox.style.borderTop = "1px solid #e5e7eb";
    riskCard.appendChild(errorBox);
  }

  errorBox.innerHTML = `
    <div style="font-size:12px; font-weight:700; color:#b91c1c; text-transform:uppercase; margin-bottom:6px;">
      Scan Error
    </div>
    <div style="font-size:12px; color:#7f1d1d;">
      ${escapeHtml(message)}
    </div>
  `;
}

function updateLocalStats(riskScore: number): void {
  const scanned = Number(localStorage.getItem(STATS_SCANNED_KEY) || "0") + 1;
  const fraud = Number(localStorage.getItem(STATS_FRAUD_KEY) || "0") + (riskScore >= 50 ? 1 : 0);

  localStorage.setItem(STATS_SCANNED_KEY, String(scanned));
  localStorage.setItem(STATS_FRAUD_KEY, String(fraud));
  loadLocalStats();
}

function loadLocalStats(): void {
  const scanned = Number(localStorage.getItem(STATS_SCANNED_KEY) || "0");
  const fraud = Number(localStorage.getItem(STATS_FRAUD_KEY) || "0");

  const scannedEl = document.getElementById("emails-scanned");
  const fraudEl = document.getElementById("fraud-detected");

  if (scannedEl) scannedEl.textContent = `${scanned.toLocaleString()} emails scanned`;
  if (fraudEl) fraudEl.textContent = `${fraud.toLocaleString()} fraud detected`;
}

function resetScanner(): void {
  const button = document.getElementById("scan-email");
  const chart = document.getElementById("scan-chart");
  const actions = document.getElementById("scan-actions");
  const pie = document.getElementById("scan-chart-pie") as HTMLElement | null;
  const safePercentText = document.getElementById("scan-safe-percent");
  const badge = document.getElementById("risk-badge") as HTMLElement | null;
  const meterFill = document.getElementById("risk-meter-fill") as HTMLElement | null;
  const score = document.getElementById("risk-score");
  const flags = document.getElementById("risk-flags");
  const links = document.getElementById("risk-links");
  const sender = document.getElementById("risk-sender");
  const credential = document.getElementById("risk-credential");
  const attachment = document.getElementById("risk-attachment");
  const summaryBox = document.getElementById("llm-summary-box");

  button?.classList.remove("hidden");
  chart?.classList.add("hidden");
  actions?.classList.add("hidden");

  if (pie) {
    pie.style.background = "conic-gradient(#22c55e 0% 80%, #ef4444 80% 100%)";
  }
  if (safePercentText) safePercentText.textContent = "80%";

  if (badge) {
    badge.textContent = "SAFE";
    badge.className = "risk-card__badge";
    badge.style.background = "#dcfce7";
    badge.style.color = "#15803d";
  }

  if (meterFill) {
    meterFill.style.width = "0%";
    meterFill.style.background = "linear-gradient(90deg, #22c55e, #84cc16)";
  }

  if (score) score.textContent = "0";
  if (flags) flags.textContent = "None";
  if (links) links.textContent = "0";
  if (sender) sender.textContent = "No";
  if (credential) credential.textContent = "No";
  if (attachment) attachment.textContent = "No";

  summaryBox?.remove();
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
