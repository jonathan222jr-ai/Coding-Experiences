// src/models/EmailModel.ts

export interface AuthSignals {
  spf?: "pass" | "fail" | "softfail" | "neutral" | "none";
  dkim?: "pass" | "fail" | "none";
  dmarc?: "pass" | "fail" | "none";
}

export interface ScannerConfig {
  /** Organization-owned domains, e.g. ["company.com", "company.org"] */
  trustedDomains?: string[];
  /** Safe sender domains you want to down-rank, e.g. github.com, jira.company.com */
  safeSenderDomains?: string[];
  /** Sensitivity multiplier. 1.0 default; recommended range 0.85..1.2 */
  sensitivity?: number;
  /** If false, obvious SAFE emails do not need LLM escalation. Default true. */
  sendLowRiskToLLM?: boolean;
  /** Risk threshold for LLM escalation. Default MEDIUM. */
  llmEscalationThreshold?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface EmailModel {
  subject: string;
  sender: string; // full sender header or plain email
  body: string;

  senderDisplayName?: string;
  senderName?: string;
  replyTo?: string;
  recipient?: string;
  cc?: string[];
  bodyHtml?: string;
  links?: string[];
  attachments?: string[];
  embeddedText?: string;
  auth?: AuthSignals;
  headers?: Record<string, string>;
  config?: ScannerConfig;
}
