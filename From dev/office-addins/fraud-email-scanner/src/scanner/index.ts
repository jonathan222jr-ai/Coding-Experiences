// src/scanner/index.ts
export { scanEmail } from "./services/scannerEngine";
export type { ScanResult } from "./services/scannerEngine";

export type { EmailModel } from "./models/EmailModel";

// optional re-exports (handy elsewhere)
export { SUSPICIOUS_KEYWORDS } from "./services/featureExtractor";
export type { Features } from "./services/featureExtractor";
export type { Flag } from "./services/ruleEngine";
export type { RiskLevel } from "./services/riskScorer";
