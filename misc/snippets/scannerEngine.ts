// src/services/scannerEngine.ts

import type { EmailModel, ScannerConfig } from "../models/EmailModel";
import { extractFeatures } from "./featureExtractor";
import type { Features, ThreatCategory } from "./featureExtractor";
import { applyRules } from "./ruleEngine";
import type { Flag } from "./ruleEngine";
import { calculateRisk } from "./riskScorer";
import type { RiskLevel } from "./riskScorer";

export interface LlmEscalationDecision {
  should_escalate: boolean;
  reason: string;
  threshold: Exclude<RiskLevel, "SAFE">;
}

export interface ScanResult {
  risk_level: RiskLevel;
  risk_score: number;
  flags: Flag[];
  dominant_categories: ThreatCategory[];
  uncertain: boolean;
  feature_summary: Features & { spoofed_domain: boolean };
  llm_escalation: LlmEscalationDecision;
}

const THRESHOLD_ORDER: Exclude<RiskLevel, "SAFE">[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

function mergeConfig(email: EmailModel): Required<ScannerConfig> {
  return {
    trustedDomains: (email.config?.trustedDomains ?? []).map((d) => d.toLowerCase()),
    safeSenderDomains: (email.config?.safeSenderDomains ?? []).map((d) => d.toLowerCase()),
    sensitivity: email.config?.sensitivity ?? 1,
    sendLowRiskToLLM: email.config?.sendLowRiskToLLM ?? false,
    llmEscalationThreshold: email.config?.llmEscalationThreshold ?? "MEDIUM",
  };
}

function meetsThreshold(level: RiskLevel, threshold: Exclude<RiskLevel, "SAFE">): boolean {
  if (level === "SAFE") return false;
  return THRESHOLD_ORDER.indexOf(level) >= THRESHOLD_ORDER.indexOf(threshold);
}

function shouldEscalateToLlm(risk: RiskLevel, uncertain: boolean, config: Required<ScannerConfig>): LlmEscalationDecision {
  const threshold = config.llmEscalationThreshold;
  const thresholdHit = meetsThreshold(risk, threshold);
  const maybeRisky = thresholdHit || uncertain;

  if (risk === "SAFE" && !config.sendLowRiskToLLM) {
    return {
      should_escalate: false,
      reason: "SAFE result below escalation policy.",
      threshold,
    };
  }

  return {
    should_escalate: maybeRisky || config.sendLowRiskToLLM,
    reason: maybeRisky
      ? "Risk threshold met or classification uncertain."
      : "Configured to escalate low-risk messages.",
    threshold,
  };
}

export function scanEmail(email: EmailModel): ScanResult {
  const config = mergeConfig(email);
  const features = extractFeatures({
    ...email,
    config,
  });
  const ruleResult = applyRules(features, config.sensitivity);
  const risk = calculateRisk(ruleResult.score);
  const llmEscalation = shouldEscalateToLlm(risk, ruleResult.uncertain, config);

  return {
    risk_level: risk,
    risk_score: ruleResult.score,
    flags: ruleResult.flags,
    dominant_categories: ruleResult.dominant_categories,
    uncertain: ruleResult.uncertain,
    feature_summary: {
      ...features,
      // Backward-compatible alias used by the task pane UI.
      spoofed_domain: features.sender_domain_mismatch || features.lookalike_domain || features.sender_displayname_domain_mismatch,
    },
    llm_escalation: llmEscalation,
  };
}
