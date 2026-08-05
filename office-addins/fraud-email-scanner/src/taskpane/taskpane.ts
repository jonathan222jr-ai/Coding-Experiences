// src/taskpane/taskpane.ts
import { scanEmail } from "../scanner";
import type { EmailModel } from "../scanner";

type ViewName = "home" | "result";

Office.onReady(() => {
  const sideloadMsg = document.getElementById("sideload-msg");
  const appBody = document.getElementById("app-body");

  if (sideloadMsg) sideloadMsg.style.display = "none";
  if (appBody) appBody.style.display = "block";

  bindClick(["scan-email", "scan-btn", "run"], runScan);
  bindClick(["back-button", "back-btn"], () => showView("home"));
  bindClick(["junk-btn"], handleSendToJunk);

  showView("home");
  setStatus("Ready to scan.");
});

function bindClick(ids: string[], handler: EventListenerOrEventListenerObject) {
  for (const id of ids) {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("click", handler);
      return;
    }
  }
}

async function runScan() {
  const item = Office.context.mailbox.item as any;

  if (!item) {
    console.error("No Outlook item available.");
    setStatus("No Outlook item available.");
    setResultText("No Outlook item available.");
    return;
  }

  try {
    setStatus("Scanning…");

    const [subject, body] = await Promise.all([getSubject(item), getBodyText(item)]);

    const sender = getSenderEmail(item);
    const senderDisplayName = getSenderDisplayName(item);
    const links = extractLinks(body);
    const attachments = getAttachmentNames(item);

    const email: EmailModel = {
      subject,
      sender,
      body,
      links,
      attachments,
      senderDisplayName,
    };

    const result = scanEmail(email);
    renderScanResult(result);
    showView("result");
    setStatus("Scan complete.");
  } catch (e) {
    console.error("Scan failed:", e);
    setStatus("Scan failed.");
    setResultText("Scan failed. Check console for details.");
  }
}

/** Outlook subject:
 * - Read mode: item.subject is a string
 * - Compose mode: item.subject.getAsync exists
 */
function getSubject(item: any): Promise<string> {
  return new Promise((resolve) => {
    if (item?.subject?.getAsync) {
      item.subject.getAsync((res: Office.AsyncResult<string>) => {
        resolve(res.status === Office.AsyncResultStatus.Succeeded ? res.value ?? "" : "");
      });
      return;
    }
    resolve((item?.subject as string) ?? "");
  });
}

/** Body text works in both read & compose using item.body.getAsync(Text) */
function getBodyText(item: any): Promise<string> {
  return new Promise((resolve, reject) => {
    item.body.getAsync(Office.CoercionType.Text, (res: Office.AsyncResult<string>) => {
      if (res.status !== Office.AsyncResultStatus.Succeeded) {
        reject(new Error("Failed to get body text."));
        return;
      }
      resolve(res.value ?? "");
    });
  });
}

/** Sender:
 * - Read mode: item.from.emailAddress exists
 * - Compose mode: you are the sender (fallback to current user)
 */
function getSenderEmail(item: any): string {
  const fromEmail = item?.from?.emailAddress;
  if (typeof fromEmail === "string" && fromEmail.length > 0) return fromEmail;

  const me = Office.context.mailbox.userProfile?.emailAddress;
  return me ?? "";
}

function getSenderDisplayName(item: any): string | undefined {
  const fromName = item?.from?.displayName;
  if (typeof fromName === "string" && fromName.length > 0) return fromName;

  const meName = Office.context.mailbox.userProfile?.displayName;
  return typeof meName === "string" && meName.length > 0 ? meName : undefined;
}

/** Attachments:
 * - Read mode usually has item.attachments[]
 * - Compose mode may also have attachments[]
 */
function getAttachmentNames(item: any): string[] {
  const atts = item?.attachments;
  if (!Array.isArray(atts)) return [];
  return atts
    .map((a: any) => a?.name)
    .filter((n: any) => typeof n === "string" && n.length > 0);
}

function extractLinks(text: string): string[] {
  const regex = /(https?:\/\/[^\s]+)/g;
  return text.match(regex) ?? [];
}

function renderScanResult(result: any) {
  const flags = Array.isArray(result.flags) ? result.flags : [];
  const riskScore = normalizeRiskScore(result.risk_score);
  const riskLevel = String(result.risk_level ?? "").toLowerCase();

  // Main result area fallback / debug panel
  const resultBox = document.getElementById("scan-result");
  if (resultBox) {
    resultBox.innerHTML = `
      <h3>Scan Results</h3>
      <p><strong>Risk Level:</strong> ${escapeHtml(String(result.risk_level ?? ""))}</p>
      <p><strong>Risk Score:</strong> ${escapeHtml(String(riskScore))}%</p>
      <p><strong>Flags:</strong> ${escapeHtml(flagsToText(flags))}</p>
    `;
  }

  // Big percentage circle
  const riskPercent = document.getElementById("risk-percent");
  if (riskPercent) {
    riskPercent.textContent = `${riskScore}%`;
  }

  const riskCircle = document.getElementById("risk-circle") ?? document.querySelector(".risk-badge");
  if (riskCircle) {
    riskCircle.classList.remove("risk-safe", "risk-low", "risk-medium", "risk-high");

    if (riskLevel === "high") {
      riskCircle.classList.add("risk-high");
    } else if (riskLevel === "medium") {
      riskCircle.classList.add("risk-medium");
    } else if (riskLevel === "low") {
      riskCircle.classList.add("risk-low");
    } else {
      riskCircle.classList.add("risk-safe");
    }
  }

  // Optional risk label text
  const riskLabelText = document.getElementById("risk-level-text");
  if (riskLabelText) {
    riskLabelText.textContent = String(result.risk_level ?? "SAFE");
  }

  // Reason bullet list
  const reasonList = document.getElementById("reason-list");
  if (reasonList) {
    reasonList.innerHTML = "";

    const reasons = flagsToReasonList(flags);
    if (reasons.length === 0) {
      const li = document.createElement("li");
      li.textContent = "No major suspicious indicators detected";
      reasonList.appendChild(li);
    } else {
      reasons.forEach((reason) => {
        const li = document.createElement("li");
        li.textContent = reason;
        reasonList.appendChild(li);
      });
    }
  }
}

function normalizeRiskScore(score: unknown): number {
  const n = Number(score);
  if (!Number.isFinite(n)) return 0;

  // supports both 0..1 and 0..100
  if (n >= 0 && n <= 1) return Math.round(n * 100);
  return Math.max(0, Math.min(100, Math.round(n)));
}

function flagsToText(flags: any[]): string {
  if (!flags.length) return "None";
  return flags.map((flag) => prettyFlag(flag)).join(", ");
}

function flagsToReasonList(flags: any[]): string[] {
  return flags
    .map((flag) => prettyFlag(flag))
    .filter((x) => typeof x === "string" && x.trim().length > 0);
}

function prettyFlag(flag: any): string {
  if (typeof flag === "string") return humanizeFlag(flag);
  if (typeof flag?.message === "string") return flag.message;
  if (typeof flag?.reason === "string") return flag.reason;
  if (typeof flag?.name === "string") return humanizeFlag(flag.name);
  if (typeof flag?.code === "string") return humanizeFlag(flag.code);
  return "";
}

function humanizeFlag(flag: string): string {
  const map: Record<string, string> = {
    multiple_links: "Multiple links detected",
    urgent_language: "Urgent language detected",
    suspicious_sender: "Suspicious sender/domain",
    html_form: "Embedded HTML form detected",
    ip_address_link: "Link uses a raw IP address",
    shortened_link: "Shortened link detected",
    suspicious_domain: "Suspicious login or verification link",
    mismatched_link: "Displayed link text may not match destination",
    credential_harvest: "Possible credential harvesting language",
    impersonation: "Possible impersonation language",
    ceo_fraud_finance_request: "Possible CEO fraud or financial request",
    qr_phishing: "Possible QR phishing language",
    vishing: "Phone or callback pressure detected",
    smishing: "SMS or mobile lure language detected",
    evil_twin_wifi: "Public Wi-Fi lure language detected",
    suspicious_attachment: "Suspicious attachment detected",
    executable_attachment: "Executable attachment detected",
    macro_attachment: "Macro-enabled attachment detected",
  };

  if (map[flag]) return map[flag];

  return flag
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function showView(view: ViewName) {
  const homeView = document.getElementById("home-view") ?? document.getElementById("view-home");
  const resultView = document.getElementById("result-view") ?? document.getElementById("view-result");

  if (!homeView || !resultView) return;

  if (view === "result") {
    homeView.style.display = "none";
    resultView.style.display = "block";
  } else {
    resultView.style.display = "none";
    homeView.style.display = "block";
  }
}

function setResultText(text: string) {
  const resultBox = document.getElementById("scan-result");
  if (!resultBox) return;
  resultBox.textContent = text;
}

function setStatus(text: string) {
  const statusEl = document.getElementById("scan-status");
  if (statusEl) statusEl.textContent = text;
}

function handleSendToJunk() {
  setStatus("Send to Junk is not connected yet.");
}

// basic safety so email content can’t inject HTML into your taskpane
function escapeHtml(s: string): string {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}