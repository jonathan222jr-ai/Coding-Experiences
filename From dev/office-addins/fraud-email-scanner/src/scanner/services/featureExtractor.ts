// src/services/featureExtractor.ts

import type { EmailModel } from "../models/EmailModel";

export const SUSPICIOUS_KEYWORDS = [
  "urgent",
  "verify",
  "immediately",
  "suspend",
  "click here",
  "limited time",
  "password",
  "bank",
  "wire",
  "transfer",
  "gift cards",
  "payroll",
  "invoice",
  "account",
  "confirm",
  "login",
  "mfa",
  "2fa",
];

export interface Features {
  // existing
  num_links: number;
  urgent_language: boolean;
  spoofed_domain: boolean;
  contains_html_form: boolean;
  has_ip_link: boolean;

  // new
  shortened_link: boolean;
  suspicious_domain: boolean;
  mismatched_link: boolean;

  credential_request: boolean;
  impersonation_language: boolean;
  finance_request: boolean;

  has_qr_code: boolean;
  vishing_language: boolean;
  smishing_language: boolean;
  evil_twin_wifi_language: boolean;

  suspicious_attachment: boolean;
  executable_attachment: boolean;
  macro_attachment: boolean;
}

function endsWithTrustedDomain(sender: string): boolean {
  // TODO: replace with your org allowlist / tenant domains
  return sender.toLowerCase().endsWith("@trustedcompany.com");
}

function containsIpUrl(text: string): boolean {
  const ipUrlRegex = /https?:\/\/\d+\.\d+\.\d+\.\d+/i;
  return ipUrlRegex.test(text);
}

function hasShortenedLink(links: string[]): boolean {
  const shorteners = [
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "buff.ly",
    "is.gd",
    "cutt.ly",
    "rebrand.ly",
    "shorturl.at",
  ];
  return links.some((l) => shorteners.some((s) => l.toLowerCase().includes(s)));
}

function containsQrCode(bodyLower: string): boolean {
  // quishing often uses “scan” phrasing even if the QR is an embedded image
  const patterns = [
    "qr code",
    "scan the qr",
    "scan qr",
    "scan this code",
    "scan the code",
    "use your camera to scan",
  ];
  return patterns.some((p) => bodyLower.includes(p));
}

function asksForCredentials(bodyLower: string): boolean {
  const patterns = [
    "confirm your password",
    "verify your account",
    "update your password",
    "enter your credentials",
    "sign in to continue",
    "login to continue",
    "re-authenticate",
    "reset your password",
    "confirm your identity",
  ];
  return patterns.some((p) => bodyLower.includes(p));
}

function impersonationLanguage(bodyLower: string, subjectLower: string): boolean {
  // CEO fraud / internal impersonation language
  const patterns = [
    "this is the ceo",
    "i'm the ceo",
    "from hr",
    "human resources",
    "it support",
    "helpdesk",
    "security team",
    "finance department",
    "accounts payable",
    "payroll",
    "do this now",
    "need this asap",
    "are you available",
    "quick favor",
    "keep this confidential",
    "do not tell anyone",
  ];
  return (
    patterns.some((p) => bodyLower.includes(p)) ||
    ["urgent", "asap", "confidential"].some((p) => subjectLower.includes(p))
  );
}

function financeRequest(bodyLower: string): boolean {
  const patterns = [
    "wire transfer",
    "bank transfer",
    "send funds",
    "transfer funds",
    "purchase gift cards",
    "buy gift cards",
    "payment urgently",
    "pay this invoice",
    "update bank details",
    "change payroll",
    "routing number",
    "account number",
    "iban",
    "swift code",
  ];
  return patterns.some((p) => bodyLower.includes(p));
}

function suspiciousDomainHeuristic(links: string[]): boolean {
  // Heuristic: login/verify/update + looks like a credential flow.
  // (Real “fake website” detection is stronger with domain allowlists + similarity checks.)
  const patterns = ["login", "verify", "update", "secure", "account", "mfa", "2fa"];
  return links.some((l) => {
    const u = l.toLowerCase();
    return u.startsWith("http") && patterns.some((p) => u.includes(p));
  });
}

function mismatchedLinkHeuristic(body: string): boolean {
  // Detect cases where anchor text shows a different domain than href.
  // 1) HTML anchors: <a href="URL">TEXT</a>
  // 2) Markdown-ish: [TEXT](URL)
  const htmlAnchor = /<a\s+[^>]*href=["']([^"']+)["'][^>]*>(.*?)<\/a>/gis;
  const mdAnchor = /\[([^\]]{1,200})\]\((https?:\/\/[^\s)]+)\)/gis;

  const extractDomain = (urlOrText: string): string | null => {
    const m = urlOrText.match(/([a-z0-9-]+\.)+[a-z]{2,}/i);
    return m ? m[0].toLowerCase() : null;
  };

  let m: RegExpExecArray | null;

  while ((m = htmlAnchor.exec(body)) !== null) {
    const href = m[1] ?? "";
    const text = m[2] ?? "";
    const hrefDomain = extractDomain(href);
    const textDomain = extractDomain(text);
    if (hrefDomain && textDomain && hrefDomain !== textDomain) return true;
  }

  while ((m = mdAnchor.exec(body)) !== null) {
    const text = m[1] ?? "";
    const href = m[2] ?? "";
    const hrefDomain = extractDomain(href);
    const textDomain = extractDomain(text);
    if (hrefDomain && textDomain && hrefDomain !== textDomain) return true;
  }

  return false;
}

function vishingLanguage(bodyLower: string): boolean {
  const patterns = [
    "voicemail",
    "call me",
    "call immediately",
    "call this number",
    "call back",
    "contact us by phone",
    "dial",
    "hotline",
    "support line",
  ];
  // also detect obvious phone numbers
  const phoneRegex = /(\+?\d{1,2}[\s-]?)?(\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}/;
  return patterns.some((p) => bodyLower.includes(p)) || phoneRegex.test(bodyLower);
}

function smishingLanguage(bodyLower: string): boolean {
  const patterns = [
    "text message",
    "sms",
    "message me",
    "reply stop",
    "reply yes",
    "mobile alert",
    "tap the link",
  ];
  return patterns.some((p) => bodyLower.includes(p));
}

function evilTwinWifiLanguage(bodyLower: string): boolean {
  const patterns = [
    "free wifi",
    "free wi-fi",
    "connect to wifi",
    "connect to wi-fi",
    "public wifi",
    "airport wifi",
    "coffee shop wifi",
    "hotel wifi",
    "mall wifi",
    "scan to connect",
  ];
  return patterns.some((p) => bodyLower.includes(p));
}

function attachmentSignals(attachments: string[] = []) {
  const lower = attachments.map((a) => (a ?? "").toLowerCase()).filter(Boolean);

  const executableExt = [".exe", ".scr", ".bat", ".cmd", ".ps1", ".js", ".vbs", ".jar"];
  const macroExt = [".docm", ".xlsm", ".pptm"];
  const archiveExt = [".zip", ".rar", ".7z", ".iso"];

  const executable_attachment = lower.some((a) => executableExt.some((e) => a.endsWith(e)));
  const macro_attachment = lower.some((a) => macroExt.some((e) => a.endsWith(e)));
  const archived = lower.some((a) => archiveExt.some((e) => a.endsWith(e)));

  const suspicious_attachment =
    executable_attachment ||
    macro_attachment ||
    archived ||
    lower.some((a) => a.endsWith(".html") || a.endsWith(".htm"));

  return { suspicious_attachment, executable_attachment, macro_attachment };
}

export function extractFeatures(email: EmailModel): Features {
  const body = email.body ?? "";
  const bodyLower = body.toLowerCase();
  const subjectLower = (email.subject ?? "").toLowerCase();
  const links = (email.links ?? []).filter(Boolean);
  const { suspicious_attachment, executable_attachment, macro_attachment } =
    attachmentSignals(email.attachments ?? []);

  return {
    // existing
    num_links: links.length,
    urgent_language: SUSPICIOUS_KEYWORDS.some((w) => bodyLower.includes(w) || subjectLower.includes(w)),
    spoofed_domain: !endsWithTrustedDomain(email.sender ?? ""),
    contains_html_form: bodyLower.includes("<form"),
    has_ip_link: containsIpUrl(bodyLower) || links.some((l) => containsIpUrl(l)),

    // new link logic
    shortened_link: hasShortenedLink(links),
    suspicious_domain: suspiciousDomainHeuristic(links),
    mismatched_link: mismatchedLinkHeuristic(body),

    // intent / content
    credential_request: asksForCredentials(bodyLower),
    impersonation_language: impersonationLanguage(bodyLower, subjectLower),
    finance_request: financeRequest(bodyLower),

    // emerging vectors
    has_qr_code: containsQrCode(bodyLower),
    vishing_language: vishingLanguage(bodyLower),
    smishing_language: smishingLanguage(bodyLower),
    evil_twin_wifi_language: evilTwinWifiLanguage(bodyLower),

    // attachments / malware
    suspicious_attachment,
    executable_attachment,
    macro_attachment,
  };
}