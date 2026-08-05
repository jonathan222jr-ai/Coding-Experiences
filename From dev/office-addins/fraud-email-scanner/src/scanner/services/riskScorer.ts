// src/services/riskScorer.ts

export type RiskLevel = "HIGH" | "MEDIUM" | "LOW" | "SAFE";

export function calculateRisk(score: number): RiskLevel {
  // tuned for the expanded rule set (score is clamped to 0..100 in ruleEngine)
  if (score >= 70) return "HIGH";
  if (score >= 40) return "MEDIUM";
  if (score >= 20) return "LOW";
  return "SAFE";
}