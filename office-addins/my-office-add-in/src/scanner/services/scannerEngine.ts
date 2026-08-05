import type { EmailModel } from "../models/EmailModel";
import { extractFeatures } from "./featureExtractor";
import { applyRules } from "./ruleEngine";
import { calculateRisk, type RiskLevel } from "./riskScorer";
import type { Features } from "./featureExtractor";
import type { Flag } from "./ruleEngine";

export interface ScanResult {
  risk_score: number;
  risk_level: RiskLevel;
  flags: Flag[];
  feature_summary: Features;
}

export function scanEmail(email: EmailModel): ScanResult {
  const features = extractFeatures(email);
  const { score, flags } = applyRules(features);
  const risk_level = calculateRisk(score);

  return {
    risk_score: score,
    risk_level,
    flags,
    feature_summary: features,
  };
}