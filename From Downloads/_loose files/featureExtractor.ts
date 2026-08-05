// src/services/featureExtractor.ts

import type { EmailModel, ScannerConfig } from "../models/EmailModel";

export type ThreatCategory =
  | "credential_phishing"
  | "bec"
  | "malware"
  | "vishing"
  | "smishing"
  | "qr_phishing"
  | "spam_marketing"
  | "extortion_or_crypto"
  | "impersonation"
  | "benign_notification";

export interface ParsedIdentity {
  raw: string;
  address: string;
  localPart: string;
  domain: string;
  displayName: string;
}

export interface Features {
  sender_address: string;
  sender_domain: string;
  sender_display_name: string;
  reply_to_address: string | null;
  reply_to_domain: string | null;
  recipient_address: string | null;
  recipient_domain: string | null;

  num_links: number;
  num_attachments: number;
  body_length: number;
  word_count: number;
  exclamation_count: number;
  uppercase_word_ratio: number;
  non_ascii_ratio: number;

  has_ip_link: boolean;
  shortened_link: boolean;
  punycode_link: boolean;
  suspicious_tld_link: boolean;
  non_https_link: boolean;
  mismatched_link: boolean;
  link_text_masking: boolean;

  sender_domain_mismatch: boolean;
  sender_displayname_domain_mismatch: boolean;
  lookalike_domain: boolean;
  external_to_internal: boolean;
  free_mail_sender: boolean;
  role_account_sender: boolean;
  suspicious_sender_localpart: boolean;

  contains_html_form: boolean;
  credential_request: boolean;
  urgent_language: boolean;
  impersonation_language: boolean;
  finance_request: boolean;
  secrecy_language: boolean;
  vishing_language: boolean;
  smishing_language: boolean;
  has_qr_code_language: boolean;
  remote_access_lure: boolean;
  invoice_theme: boolean;
  payment_theme: boolean;
  attachment_lure_language: boolean;
  crypto_or_extortion_language: boolean;
  marketing_spam_language: boolean;

  suspicious_attachment: boolean;
  executable_attachment: boolean;
  macro_attachment: boolean;
  archive_attachment: boolean;
  html_attachment: boolean;
  suspicious_attachment_name: boolean;

  auth_failure: boolean;
  reply_to_mismatch: boolean;
  recipient_targeting: boolean;

  safe_mailing_list_signal: boolean;
  safe_thread_signal: boolean;
  safe_dev_notification_signal: boolean;
  safe_transactional_signal: boolean;
  safe_sender_allowlist_signal: boolean;

  lexical_phishing_score: number;
  lexical_ham_score: number;
  categories: ThreatCategory[];
}

const SUSPICIOUS_TLDS = new Set([
  "zip","mov","click","top","gq","tk","work","country","xin","support","live","rest","fit","cam","uno","pw","buzz","monster","party","info"
]);

const URL_SHORTENERS = new Set([
  "bit.ly","tinyurl.com","t.co","goo.gl","ow.ly","buff.ly","is.gd","cutt.ly","rebrand.ly","shorturl.at","tiny.cc","lnkd.in","rb.gy","bit.do"
]);

const FREE_MAIL_DOMAINS = new Set([
  "gmail.com","yahoo.com","hotmail.com","outlook.com","aol.com","icloud.com","proton.me","protonmail.com","mail.com","gmx.com","live.com"
]);

const SAFE_LIST_PATTERNS = [
  "mailing list","list-id:","unsubscribe","manage preferences","listinfo","mailman","bugzilla","jira","issues.apache.org","svn commit","git commit",
  "pull request","merge request","submission-id","virustotal","virus total","buildbot","ci pipeline","ticket updated"
];

const SAFE_TRANSACTIONAL_PATTERNS = [
  "order shipped","tracking number","receipt","your statement is ready","calendar invite","meeting invitation","password reset you requested"
];

const SAFE_SUBJECT_PREFIXES = ["re:","fwd:","fw:","aw:","sv:","[jira]","[bug "];

const URGENCY_PATTERNS = [
  "urgent","immediately","asap","action required","final notice","act now","right away","within 24 hours","suspended","suspension","failure to respond",
  "avoid interruption","respond today","urgent attention"
];

const CREDENTIAL_PATTERNS = [
  "verify your account","confirm your account","confirm your identity","validate your mailbox","password expires","reset your password","enter your password",
  "sign in to continue","login to continue","re-authenticate","mfa","2fa","one-time password","otp","security check","webmail verification",
  "keep your mailbox active","account verification"
];

const BEC_PATTERNS = [
  "are you available","quick favor","kindly handle this","keep this confidential","do not tell anyone","i need you to","let me know when done",
  "this is the ceo","i'm the ceo","from hr","helpdesk","security team","finance department","accounts payable","kindly purchase"
];

const FINANCE_PATTERNS = [
  "wire transfer","bank transfer","gift card","buy gift cards","payment","invoice","routing number","account number","iban","swift code",
  "change payroll","change bank details","remittance","outstanding balance","purchase order","rfq","vendor setup","payment update"
];

const VISHING_PATTERNS = [
  "voicemail","call me","call us","call immediately","call this number","call back","dial","hotline","support line","speak to representative","contact support"
];

const SMISHING_PATTERNS = [
  "text message","sms","mobile alert","tap the link","reply yes","reply stop","mobile verification","phone verification"
];

const QR_PATTERNS = ["qr code","scan the qr","scan qr","scan this code","scan the code","use your camera to scan"];

const REMOTE_ACCESS_PATTERNS = ["anydesk","teamviewer","quick assist","screenconnect","connectwise","remote desktop","install software","screen share"];

const EXTORTION_PATTERNS = ["bitcoin","btc","wallet","sextortion","i recorded you","private video","pay in cryptocurrency"];

const MARKETING_PATTERNS = [
  "daily top","special offer","free trial","replica watches","male enhancement","discount","limited offer","weight loss","mortgage","casino","loan approval"
];

const INVOICE_PATTERNS = ["invoice attached","see attached invoice","purchase order attached","remittance advice","payment receipt attached"];
const ATTACHMENT_LURE_PATTERNS = ["see attached","open attachment","attached document","download the attached","secure document"];

const ROLE_ACCOUNTS = ["admin","administrator","billing","finance","hr","humanresources","helpdesk","it","legal","payroll","security","support","accounts","ap","ar","ceo","cfo","coo"];
const SUSPICIOUS_LOCALPART_PATTERNS = [/^[a-z]{1,3}\d{3,}$/i,/^[a-z0-9._%+-]{14,}$/i,/service\d+/i,/verify/i,/secure/i,/update/i];

const EXECUTABLE_EXT = [".exe", ".scr", ".bat", ".cmd", ".ps1", ".js", ".vbs", ".jar", ".msi", ".hta"];
const MACRO_EXT = [".docm", ".xlsm", ".pptm", ".xlam"];
const ARCHIVE_EXT = [".zip", ".rar", ".7z", ".iso", ".img"];
const HTML_EXT = [".html", ".htm", ".shtml"];

function normalizeText(...parts: Array<string | undefined | null>): string {
  return parts.filter(Boolean).join("\n").toLowerCase();
}

function toAsciiUnsafe(s: string): string {
  return s.normalize("NFKD").replace(/[^\x00-\x7F]/g, "");
}

function ratio(numerator: number, denominator: number): number {
  return denominator > 0 ? numerator / denominator : 0;
}

export function parseIdentity(rawValue?: string | null, explicitDisplayName?: string | null): ParsedIdentity {
  const raw = (rawValue ?? "").trim();
  const match = raw.match(/^(?:"?([^"<]*)"?\s*)?<([^>]+)>$/) ?? raw.match(/([\w.+\-'"`]+@[\w.-]+\.[A-Za-z]{2,})/);
  const address = (match?.[2] ?? match?.[1] ?? raw).trim().toLowerCase();
  const safeAddress = /@/.test(address) ? address : "";
  const localPart = safeAddress.includes("@") ? safeAddress.split("@")[0] : "";
  const domain = safeAddress.includes("@") ? safeAddress.split("@").slice(1).join("@") : "";
  const displayName = (explicitDisplayName ?? (raw.includes("<") ? (raw.match(/^(.*)</)?.[1] ?? "") : "")).replace(/^"|"$/g, "").trim();
  return { raw, address: safeAddress, localPart, domain, displayName };
}

function extractDomainFromUrl(url: string): string {
  try {
    if (/^https?:\/\//i.test(url.trim())) {
      return new URL(url.trim()).hostname.toLowerCase();
    }
  } catch {}
  const m = url.match(/([a-z0-9-]+\.)+[a-z]{2,}/i);
  return m ? m[0].toLowerCase() : "";
}

function extractRootDomain(domain: string): string {
  const value = domain.toLowerCase().replace(/^\.+|\.+$/g, "");
  if (!value) return "";
  const parts = value.split(".");
  if (parts.length <= 2) return value;
  const multi = new Set(["co.uk","org.uk","gov.uk","ac.uk","com.au","net.au","org.au"]);
  const tail2 = parts.slice(-2).join(".");
  const tail3 = parts.slice(-3).join(".");
  if (multi.has(tail2) && parts.length >= 3) return tail3;
  return parts.slice(-2).join(".");
}

function extractUrls(email: EmailModel): string[] {
  const provided = (email.links ?? []).map((s) => s.trim()).filter(Boolean);
  if (provided.length) return Array.from(new Set(provided));
  const raw = `${email.bodyHtml ?? ""}\n${email.body ?? ""}`;
  const matches = raw.match(/https?:\/\/[^\s"'<>()[\]]+/gi) ?? [];
  return Array.from(new Set(matches));
}

function countPatternHits(text: string, patterns: string[]): number {
  return patterns.reduce((sum, p) => sum + (text.includes(p) ? 1 : 0), 0);
}

function hasPhoneNumber(text: string): boolean {
  return /(\+?\d{1,2}[\s().-]?)?(\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}/.test(text);
}

function containsIpUrl(text: string): boolean {
  return /https?:\/\/\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?(?:[/?#]|$)/i.test(text);
}

function hasLinkMasking(body: string, bodyHtml?: string): { mismatched: boolean; masking: boolean } {
  const source = `${bodyHtml ?? ""}\n${body}`;
  const htmlAnchor = /<a\s+[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  const mdAnchor = /\[([^\]]{1,200})\]\((https?:\/\/[^\s)]+)\)/gi;
  const domainFromText = (value: string) => {
    const m = toAsciiUnsafe(value).match(/([a-z0-9-]+\.)+[a-z]{2,}/i);
    return m ? m[0].toLowerCase() : "";
  };
  let mismatched = false;
  let masking = false;
  let m: RegExpExecArray | null;
  while ((m = htmlAnchor.exec(source)) !== null) {
    const hrefDomain = domainFromText(m[1] ?? "");
    const textDomain = domainFromText(m[2] ?? "");
    if (hrefDomain && textDomain && extractRootDomain(hrefDomain) !== extractRootDomain(textDomain)) mismatched = true;
    if (!textDomain && /(verify|login|view document|open|download|click here|review)/i.test(m[2] ?? "") && hrefDomain) masking = true;
  }
  while ((m = mdAnchor.exec(source)) !== null) {
    const hrefDomain = domainFromText(m[2] ?? "");
    const textDomain = domainFromText(m[1] ?? "");
    if (hrefDomain && textDomain && extractRootDomain(hrefDomain) !== extractRootDomain(textDomain)) mismatched = true;
    if (!textDomain && /(verify|login|view document|open|download|click here|review)/i.test(m[1] ?? "") && hrefDomain) masking = true;
  }
  return { mismatched, masking };
}

function looksLikeDomainImpersonation(senderDomain: string, trustedDomains: string[]): boolean {
  if (!senderDomain || !trustedDomains.length) return false;
  const asciiSender = toAsciiUnsafe(senderDomain.toLowerCase());
  return trustedDomains.some((trusted) => {
    const asciiTrusted = toAsciiUnsafe(trusted.toLowerCase());
    if (extractRootDomain(asciiSender) === extractRootDomain(asciiTrusted)) return false;
    const a = asciiSender.replace(/[.-]/g, "");
    const b = asciiTrusted.replace(/[.-]/g, "");
    if (a.includes(b) || b.includes(a)) return true;
    let diff = 0;
    for (let i = 0; i < Math.min(a.length, b.length); i += 1) {
      if (a[i] !== b[i]) diff += 1;
    }
    diff += Math.abs(a.length - b.length);
    return Math.max(a.length, b.length) >= 5 && diff <= 2;
  });
}

function attachmentSignals(attachments: string[] = []) {
  const lower = attachments.map((a) => (a ?? "").toLowerCase()).filter(Boolean);
  const executable_attachment = lower.some((a) => EXECUTABLE_EXT.some((e) => a.endsWith(e)));
  const macro_attachment = lower.some((a) => MACRO_EXT.some((e) => a.endsWith(e)));
  const archive_attachment = lower.some((a) => ARCHIVE_EXT.some((e) => a.endsWith(e)));
  const html_attachment = lower.some((a) => HTML_EXT.some((e) => a.endsWith(e)));
  const suspicious_attachment_name = lower.some((a) => /invoice|payment|remittance|purchase order|rfq|secure message|document|copy|scan/.test(a));
  return {
    executable_attachment,
    macro_attachment,
    archive_attachment,
    html_attachment,
    suspicious_attachment_name,
    suspicious_attachment: executable_attachment || macro_attachment || archive_attachment || html_attachment || suspicious_attachment_name,
  };
}

function computeLexicalScores(text: string): { phishing: number; ham: number } {
  let phishing = 0;
  let ham = 0;
  phishing += countPatternHits(text, URGENCY_PATTERNS) * 4;
  phishing += countPatternHits(text, CREDENTIAL_PATTERNS) * 7;
  phishing += countPatternHits(text, BEC_PATTERNS) * 6;
  phishing += countPatternHits(text, FINANCE_PATTERNS) * 7;
  phishing += countPatternHits(text, VISHING_PATTERNS) * 4;
  phishing += countPatternHits(text, SMISHING_PATTERNS) * 3;
  phishing += countPatternHits(text, QR_PATTERNS) * 4;
  phishing += countPatternHits(text, REMOTE_ACCESS_PATTERNS) * 7;
  phishing += countPatternHits(text, EXTORTION_PATTERNS) * 7;
  phishing += countPatternHits(text, MARKETING_PATTERNS) * 4;
  phishing += /\b(click here|confirm|verify|password|login|bank|wallet)\b/.test(text) ? 4 : 0;
  ham += countPatternHits(text, SAFE_LIST_PATTERNS) * 5;
  ham += countPatternHits(text, SAFE_TRANSACTIONAL_PATTERNS) * 4;
  ham += /\b(issue|ticket|patch|commit|release|bug|build|ci|test suite|mailing list|unsubscribe|manage preferences|calendar invite)\b/.test(text) ? 4 : 0;
  return { phishing, ham };
}

function mergeConfig(email: EmailModel): Required<ScannerConfig> {
  return {
    trustedDomains: (email.config?.trustedDomains ?? []).map((d) => d.toLowerCase()),
    safeSenderDomains: (email.config?.safeSenderDomains ?? []).map((d) => d.toLowerCase()),
    sensitivity: email.config?.sensitivity ?? 1,
    sendLowRiskToLLM: email.config?.sendLowRiskToLLM ?? false,
    llmEscalationThreshold: email.config?.llmEscalationThreshold ?? "MEDIUM",
  };
}

export function extractFeatures(email: EmailModel): Features {
  const config = mergeConfig(email);
  const sender = parseIdentity(email.sender, email.senderDisplayName ?? email.senderName);
  const replyTo = parseIdentity(email.replyTo);
  const recipient = parseIdentity(email.recipient);
  const subject = email.subject ?? "";
  const body = email.body ?? "";
  const fullText = normalizeText(subject, body, email.bodyHtml, email.embeddedText);
  const subjectLower = subject.toLowerCase();
  const links = extractUrls(email);
  const senderRoot = extractRootDomain(sender.domain);
  const recipientRoot = extractRootDomain(recipient.domain);
  const trustedRoots = config.trustedDomains.map(extractRootDomain);
  const { mismatched, masking } = hasLinkMasking(body, email.bodyHtml);
  const attachment = attachmentSignals(email.attachments ?? []);
  const lexical = computeLexicalScores(fullText);

  const auth_failure = email.auth?.spf === "fail" || email.auth?.spf === "softfail" || email.auth?.dkim === "fail" || email.auth?.dmarc === "fail";
  const sender_domain_mismatch = trustedRoots.length > 0 && senderRoot !== "" && !trustedRoots.includes(senderRoot);
  const displayLooksTrusted = config.trustedDomains.some((d) => sender.displayName.toLowerCase().includes(d.split(".")[0]));
  const sender_displayname_domain_mismatch = Boolean(sender.displayName) && displayLooksTrusted && sender_domain_mismatch;
  const reply_to_mismatch = Boolean(replyTo.address) && extractRootDomain(replyTo.domain) !== "" && extractRootDomain(replyTo.domain) !== senderRoot;
  const external_to_internal = Boolean(recipientRoot) && trustedRoots.includes(recipientRoot) && senderRoot !== "" && !trustedRoots.includes(senderRoot);

  const bodyWords = fullText.match(/[A-Za-z0-9_-]+/g) ?? [];
  const uppercaseWords = bodyWords.filter((w) => /^[A-Z0-9]{4,}$/.test(w)).length;
  const nonAsciiChars = (fullText.match(/[^\x00-\x7F]/g) ?? []).length;

  const credential_request = countPatternHits(fullText, CREDENTIAL_PATTERNS) > 0 || /\b(password|verify|login|sign in|security code|otp|webmail)\b/.test(fullText);
  const urgency = countPatternHits(fullText, URGENCY_PATTERNS) > 0;
  const bec = countPatternHits(fullText, BEC_PATTERNS) > 0;
  const finance = countPatternHits(fullText, FINANCE_PATTERNS) > 0;
  const vishing = countPatternHits(fullText, VISHING_PATTERNS) > 0 || hasPhoneNumber(fullText);
  const smishing = countPatternHits(fullText, SMISHING_PATTERNS) > 0;
  const qr = countPatternHits(fullText, QR_PATTERNS) > 0;
  const remote = countPatternHits(fullText, REMOTE_ACCESS_PATTERNS) > 0;
  const extortion = countPatternHits(fullText, EXTORTION_PATTERNS) > 0;
  const marketing = countPatternHits(fullText, MARKETING_PATTERNS) > 0;
  const invoiceTheme = countPatternHits(fullText, INVOICE_PATTERNS) > 0 || /\binvoice\b/.test(fullText);
  const attachmentLure = countPatternHits(fullText, ATTACHMENT_LURE_PATTERNS) > 0;

  const safe_mailing_list_signal = SAFE_LIST_PATTERNS.some((p) => fullText.includes(p)) || /^list-|^bounce-/.test(sender.localPart) || sender.localPart.includes("noreply");
  const safe_thread_signal = SAFE_SUBJECT_PREFIXES.some((p) => subjectLower.startsWith(p)) || /^>/.test(body.trim());
  const safe_dev_notification_signal = /\b(git|github|gitlab|jira|apache|python|bugzilla|ticket|ci|build|patch|release)\b/.test(fullText) || config.safeSenderDomains.includes(sender.domain);
  const safe_transactional_signal = SAFE_TRANSACTIONAL_PATTERNS.some((p) => fullText.includes(p));
  const safe_sender_allowlist_signal = config.safeSenderDomains.includes(sender.domain);

  const categories: ThreatCategory[] = [];
  if (credential_request) categories.push("credential_phishing");
  if (bec || finance || sender_displayname_domain_mismatch) categories.push("bec");
  if (attachment.executable_attachment || attachment.macro_attachment || attachment.archive_attachment || remote) categories.push("malware");
  if (vishing) categories.push("vishing");
  if (smishing) categories.push("smishing");
  if (qr) categories.push("qr_phishing");
  if (marketing) categories.push("spam_marketing");
  if (extortion) categories.push("extortion_or_crypto");
  if (sender_displayname_domain_mismatch || reply_to_mismatch || looksLikeDomainImpersonation(sender.domain, config.trustedDomains)) categories.push("impersonation");
  if (safe_mailing_list_signal || safe_dev_notification_signal || safe_transactional_signal) categories.push("benign_notification");

  return {
    sender_address: sender.address,
    sender_domain: sender.domain,
    sender_display_name: sender.displayName,
    reply_to_address: replyTo.address || null,
    reply_to_domain: replyTo.domain || null,
    recipient_address: recipient.address || null,
    recipient_domain: recipient.domain || null,

    num_links: links.length,
    num_attachments: (email.attachments ?? []).length,
    body_length: body.length,
    word_count: bodyWords.length,
    exclamation_count: (fullText.match(/!/g) ?? []).length,
    uppercase_word_ratio: ratio(uppercaseWords, bodyWords.length),
    non_ascii_ratio: ratio(nonAsciiChars, fullText.length),

    has_ip_link: containsIpUrl(fullText) || links.some((l) => containsIpUrl(l)),
    shortened_link: links.some((l) => URL_SHORTENERS.has(extractDomainFromUrl(l))),
    punycode_link: links.some((l) => /xn--/i.test(l) || /%[a-f0-9]{2}/i.test(l)),
    suspicious_tld_link: links.some((l) => SUSPICIOUS_TLDS.has((extractDomainFromUrl(l).split(".").pop() ?? "").toLowerCase())),
    non_https_link: links.some((l) => /^http:\/\//i.test(l)),
    mismatched_link: mismatched,
    link_text_masking: masking,

    sender_domain_mismatch,
    sender_displayname_domain_mismatch,
    lookalike_domain: looksLikeDomainImpersonation(sender.domain, config.trustedDomains),
    external_to_internal,
    free_mail_sender: FREE_MAIL_DOMAINS.has(sender.domain),
    role_account_sender: ROLE_ACCOUNTS.some((role) => sender.localPart.replace(/[^a-z]/g, "") === role || sender.localPart.replace(/[^a-z]/g, "").startsWith(role)),
    suspicious_sender_localpart: SUSPICIOUS_LOCALPART_PATTERNS.some((rx) => rx.test(sender.localPart)),

    contains_html_form: /<form\b/i.test(email.bodyHtml ?? body),
    credential_request,
    urgent_language: urgency,
    impersonation_language: bec,
    finance_request: finance,
    secrecy_language: /confidential|do not share|secret|discreetly|privately/.test(fullText),
    vishing_language: vishing,
    smishing_language: smishing,
    has_qr_code_language: qr,
    remote_access_lure: remote,
    invoice_theme: invoiceTheme,
    payment_theme: /\b(payment|remittance|bank|invoice|vendor)\b/.test(fullText),
    attachment_lure_language: attachmentLure,
    crypto_or_extortion_language: extortion,
    marketing_spam_language: marketing,

    suspicious_attachment: attachment.suspicious_attachment,
    executable_attachment: attachment.executable_attachment,
    macro_attachment: attachment.macro_attachment,
    archive_attachment: attachment.archive_attachment,
    html_attachment: attachment.html_attachment,
    suspicious_attachment_name: attachment.suspicious_attachment_name,

    auth_failure,
    reply_to_mismatch,
    recipient_targeting: Boolean(recipient.address) && fullText.includes(recipient.address.toLowerCase()),

    safe_mailing_list_signal,
    safe_thread_signal,
    safe_dev_notification_signal,
    safe_transactional_signal,
    safe_sender_allowlist_signal,

    lexical_phishing_score: lexical.phishing,
    lexical_ham_score: lexical.ham,
    categories: Array.from(new Set(categories)),
  };
}
