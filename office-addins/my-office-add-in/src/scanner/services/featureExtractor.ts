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
];

export interface Features {
  num_links: number;
  urgent_language: boolean;
  spoofed_domain: boolean;
  contains_html_form: boolean;
  has_ip_link: boolean;
}

function endsWithTrustedDomain(sender: string): boolean {
  // Matches your Python: not email.sender.endswith("@trustedcompany.com") :contentReference[oaicite:2]{index=2}
  return sender.toLowerCase().endsWith("@trustedcompany.com");
}

function containsIpUrl(text: string): boolean {
  // Matches your regex: http[s]?://\d+\.\d+\.\d+\.\d+ :contentReference[oaicite:3]{index=3}
  const ipUrlRegex = /https?:\/\/\d+\.\d+\.\d+\.\d+/i;
  return ipUrlRegex.test(text);
}

export function extractFeatures(email: EmailModel): Features {
  const body = (email.body ?? "").toLowerCase();
  const subject = (email.subject ?? "").toLowerCase(); // kept for parity even if not used
  void subject;

  const links = email.links ?? [];

  return {
    num_links: links.length,
    urgent_language: SUSPICIOUS_KEYWORDS.some((word) => body.includes(word)),
    spoofed_domain: !endsWithTrustedDomain(email.sender ?? ""),
    contains_html_form: body.includes("<form"),
    has_ip_link:
      containsIpUrl(body) || links.some((link) => containsIpUrl(link ?? "")),
  };
}