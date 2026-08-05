// src/services/scannerEngine.ts

import type { EmailModel } from "../models/EmailModel";
import { extractFeatures, type Features } from "./featureExtractor";
import { applyRules, type Flag } from "./ruleEngine";
import { calculateRisk, type RiskLevel } from "./riskScorer";

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