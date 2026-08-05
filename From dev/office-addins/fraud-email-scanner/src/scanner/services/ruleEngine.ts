// src/services/ruleEngine.ts

import type { Features } from "./featureExtractor";

export type Flag =
  | "multiple_links"
  | "urgent_language"
  | "suspicious_sender"
  | "html_form"
  | "ip_address_link"
  | "shortened_link"
  | "suspicious_domain"
  | "mismatched_link"
  | "credential_harvest"
  | "impersonation"
  | "ceo_fraud_finance_request"
  | "qr_phishing"
  | "vishing"
  | "smishing"
  | "evil_twin_wifi"
  | "suspicious_attachment"
  | "executable_attachment"
  | "macro_attachment";

export function applyRules(features: Features): { score: number; flags: Flag[] } {
  let score = 0;
  const flags: Flag[] = [];

  // Link-based
  if (features.num_links > 2) {
    score += 10;
    flags.push("multiple_links");
  }
  if (features.has_ip_link) {
    score += 25;
    flags.push("ip_address_link");
  }
  if (features.shortened_link) {
    score += 15;
    flags.push("shortened_link");
  }
  if (features.suspicious_domain) {
    score += 20;
    flags.push("suspicious_domain");
  }
  if (features.mismatched_link) {
    score += 25;
    flags.push("mismatched_link");
  }

  // Sender + language
  if (features.spoofed_domain) {
    score += 20;
    flags.push("suspicious_sender");
  }
  if (features.urgent_language) {
    score += 15;
    flags.push("urgent_language");
  }

  // Credential / content injection
  if (features.contains_html_form) {
    score += 20;
    flags.push("html_form");
  }
  if (features.credential_request) {
    score += 30;
    flags.push("credential_harvest");
  }

  // Spear phishing / CEO fraud indicators
  if (features.impersonation_language) {
    score += 25;
    flags.push("impersonation");
  }
  if (features.impersonation_language && features.finance_request) {
    score += 35;
    flags.push("ceo_fraud_finance_request");
  }

  // Quishing / mobile / voice vectors
  if (features.has_qr_code) {
    score += 25;
    flags.push("qr_phishing");
  }
  if (features.vishing_language) {
    score += 15;
    flags.push("vishing");
  }
  if (features.smishing_language) {
    score += 10;
    flags.push("smishing");
  }
  if (features.evil_twin_wifi_language) {
    score += 15;
    flags.push("evil_twin_wifi");
  }

  // Malware / attachments
  if (features.suspicious_attachment) {
    score += 25;
    flags.push("suspicious_attachment");
  }
  if (features.executable_attachment) {
    score += 35;
    flags.push("executable_attachment");
  }
  if (features.macro_attachment) {
    score += 25;
    flags.push("macro_attachment");
  }

  // Clamp score (optional, but helps keep scoring sane)
  if (score > 100) score = 100;

  return { score, flags };
}