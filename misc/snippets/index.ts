// src/scanner/index.ts
export { scanEmail } from "./services/scannerEngine";
export type { ScanResult, LlmEscalationDecision } from "./services/scannerEngine";
export type { EmailModel, AuthSignals, ScannerConfig } from "./models/EmailModel";
export type { Features, ThreatCategory, ParsedIdentity } from "./services/featureExtractor";
export type { Flag, Finding, RuleResult } from "./services/ruleEngine";
export type { RiskLevel } from "./services/riskScorer";
