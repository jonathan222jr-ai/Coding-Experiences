// src/services/ruleEngine.ts

import type { Features, ThreatCategory } from "./featureExtractor";

export type Flag =
  | "multiple_links"
  | "ip_address_link"
  | "shortened_link"
  | "punycode_link"
  | "suspicious_tld_link"
  | "non_https_link"
  | "mismatched_link"
  | "link_text_masking"
  | "suspicious_sender"
  | "sender_name_mismatch"
  | "reply_to_mismatch"
  | "lookalike_domain"
  | "free_mail_sender"
  | "role_account_sender"
  | "suspicious_sender_localpart"
  | "external_to_internal"
  | "auth_failure"
  | "html_form"
  | "credential_harvest"
  | "urgent_language"
  | "impersonation"
  | "finance_request"
  | "secrecy_language"
  | "ceo_fraud_finance_request"
  | "qr_phishing"
  | "vishing"
  | "smishing"
  | "remote_access_lure"
  | "invoice_theme"
  | "attachment_lure"
  | "crypto_or_extortion"
  | "marketing_spam"
  | "suspicious_attachment"
  | "executable_attachment"
  | "macro_attachment"
  | "archive_attachment"
  | "html_attachment"
  | "recipient_targeting"
  | "likely_mailing_list"
  | "likely_dev_notification"
  | "safe_thread_context"
  | "safe_transactional"
  | "safe_sender_allowlist";

export interface Finding {
  flag: Flag;
  weight: number;
  reason: string;
}

export interface RuleResult {
  score: number;
  flags: Flag[];
  findings: Finding[];
  dominant_categories: ThreatCategory[];
  uncertain: boolean;
}

function push(findings: Finding[], flag: Flag, weight: number, reason: string): number {
  findings.push({ flag, weight, reason });
  return weight;
}

export function applyRules(features: Features, sensitivity = 1): RuleResult {
  let score = 0;
  const findings: Finding[] = [];
  const categories = new Set<ThreatCategory>(features.categories);

  if (features.num_links >= 3) score += push(findings, "multiple_links", 8, "Email contains several links.");
  if (features.has_ip_link) score += push(findings, "ip_address_link", 22, "Link points to a raw IP address.");
  if (features.shortened_link) score += push(findings, "shortened_link", 12, "Shortened URL hides the final destination.");
  if (features.punycode_link) score += push(findings, "punycode_link", 20, "Link may use IDN or punycode masking.");
  if (features.suspicious_tld_link) score += push(findings, "suspicious_tld_link", 14, "Link uses a risky or uncommon TLD.");
  if (features.non_https_link) score += push(findings, "non_https_link", 6, "At least one link is not HTTPS.");
  if (features.mismatched_link) score += push(findings, "mismatched_link", 24, "Displayed link text and destination do not match.");
  if (features.link_text_masking) score += push(findings, "link_text_masking", 14, "Link label hides the actual destination.");

  if (features.sender_domain_mismatch) score += push(findings, "suspicious_sender", 12, "Sender domain is outside trusted organization domains.");
  if (features.sender_displayname_domain_mismatch) score += push(findings, "sender_name_mismatch", 20, "Display name suggests a trusted brand or org, but domain does not match.");
  if (features.reply_to_mismatch) score += push(findings, "reply_to_mismatch", 18, "Reply-To domain differs from sender domain.");
  if (features.lookalike_domain) score += push(findings, "lookalike_domain", 24, "Sender domain resembles a trusted domain.");
  if (features.free_mail_sender) score += push(findings, "free_mail_sender", 6, "Sender uses a free-mail provider.");
  if (features.role_account_sender) score += push(findings, "role_account_sender", 6, "Sender local part looks like a role account.");
  if (features.suspicious_sender_localpart) score += push(findings, "suspicious_sender_localpart", 8, "Sender local part looks randomly generated or security-themed.");
  if (features.external_to_internal) score += push(findings, "external_to_internal", 8, "Message is external but targets an internal recipient.");
  if (features.auth_failure) score += push(findings, "auth_failure", 28, "SPF, DKIM, or DMARC indicates a failure.");

  if (features.contains_html_form) score += push(findings, "html_form", 22, "Message contains an HTML form.");
  if (features.credential_request) score += push(findings, "credential_harvest", 26, "Message asks for authentication or identity confirmation.");
  if (features.urgent_language) score += push(findings, "urgent_language", 10, "Urgency language pressures the recipient.");
  if (features.impersonation_language) score += push(findings, "impersonation", 14, "Language resembles internal impersonation or BEC.");
  if (features.finance_request) score += push(findings, "finance_request", 18, "Message requests payment, transfer, or account changes.");
  if (features.secrecy_language) score += push(findings, "secrecy_language", 10, "Message asks for secrecy or discretion.");
  if (features.has_qr_code_language) score += push(findings, "qr_phishing", 14, "Message mentions QR-code based action.");
  if (features.vishing_language) score += push(findings, "vishing", 10, "Voice-contact lure detected.");
  if (features.smishing_language) score += push(findings, "smishing", 8, "SMS or mobile verification lure detected.");
  if (features.remote_access_lure) score += push(findings, "remote_access_lure", 22, "Remote access software lure detected.");
  if (features.invoice_theme) score += push(findings, "invoice_theme", 9, "Invoice or payment-document theme detected.");
  if (features.attachment_lure_language) score += push(findings, "attachment_lure", 8, "Message urges the user to open an attachment.");
  if (features.crypto_or_extortion_language) score += push(findings, "crypto_or_extortion", 18, "Crypto-payment or extortion language detected.");
  if (features.marketing_spam_language) score += push(findings, "marketing_spam", 8, "Bulk marketing or commodity-spam language detected.");

  if (features.suspicious_attachment) score += push(findings, "suspicious_attachment", 16, "Attachment type or name is suspicious.");
  if (features.executable_attachment) score += push(findings, "executable_attachment", 32, "Executable attachment detected.");
  if (features.macro_attachment) score += push(findings, "macro_attachment", 24, "Macro-enabled document detected.");
  if (features.archive_attachment) score += push(findings, "archive_attachment", 12, "Archive attachment can hide payloads.");
  if (features.html_attachment) score += push(findings, "html_attachment", 18, "HTML attachment can be used for credential theft.");

  if (features.recipient_targeting) score += push(findings, "recipient_targeting", 6, "Email appears tailored to the recipient.");

  if (features.impersonation_language && features.finance_request) {
    score += push(findings, "ceo_fraud_finance_request", 28, "Impersonation plus financial request strongly suggests BEC.");
  }
  if (features.credential_request && (features.mismatched_link || features.reply_to_mismatch || features.auth_failure || features.sender_displayname_domain_mismatch)) {
    score += 18;
  }
  if (features.remote_access_lure && features.vishing_language) {
    score += 14;
  }
  if (features.invoice_theme && (features.suspicious_attachment || features.mismatched_link || features.reply_to_mismatch)) {
    score += 16;
  }
  if (features.crypto_or_extortion_language && features.urgent_language) {
    score += 10;
  }
  if (features.exclamation_count >= 3) score += 3;
  if (features.uppercase_word_ratio >= 0.08) score += 4;
  if (features.non_ascii_ratio >= 0.03) score += 4;

  score += Math.min(30, Math.max(0, features.lexical_phishing_score - Math.round(features.lexical_ham_score * 0.6)));

  if (features.safe_mailing_list_signal) score += push(findings, "likely_mailing_list", -20, "Mailing-list or newsletter indicators reduce risk.");
  if (features.safe_dev_notification_signal) score += push(findings, "likely_dev_notification", -16, "Developer or issue-tracker notification indicators reduce risk.");
  if (features.safe_thread_signal) score += push(findings, "safe_thread_context", -6, "Existing thread or reply context reduces risk slightly.");
  if (features.safe_transactional_signal) score += push(findings, "safe_transactional", -10, "Known transactional-message patterns reduce risk slightly.");
  if (features.safe_sender_allowlist_signal) score += push(findings, "safe_sender_allowlist", -18, "Sender domain is explicitly allowlisted.");

  score = Math.round(score * sensitivity);
  score = Math.max(0, Math.min(100, score));

  const uncertain =
    (score >= 18 && score <= 40) ||
    (categories.has("benign_notification") && score >= 22) ||
    (categories.has("credential_phishing") && features.safe_mailing_list_signal) ||
    (findings.filter((f) => f.weight > 0).length >= 4 && findings.filter((f) => f.weight < 0).length >= 2);

  return {
    score,
    flags: findings.filter((f) => f.weight > 0).map((f) => f.flag),
    findings,
    dominant_categories: Array.from(categories),
    uncertain,
  };
}
