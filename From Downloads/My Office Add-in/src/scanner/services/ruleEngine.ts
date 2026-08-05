import type { Features } from "./featureExtractor";

export type Flag =
  | "multiple_links"
  | "urgent_language"
  | "suspicious_sender"
  | "html_form"
  | "ip_address_link";

export function applyRules(features: Features): { score: number; flags: Flag[] } {
  let score = 0;
  const flags: Flag[] = [];

  if (features.num_links > 2) {
    score += 15;
    flags.push("multiple_links");
  }

  if (features.urgent_language) {
    score += 20;
    flags.push("urgent_language");
  }

  if (features.spoofed_domain) {
    score += 25;
    flags.push("suspicious_sender");
  }

  if (features.contains_html_form) {
    score += 20;
    flags.push("html_form");
  }

  if (features.has_ip_link) {
    score += 30;
    flags.push("ip_address_link");
  }

  return { score, flags };
}