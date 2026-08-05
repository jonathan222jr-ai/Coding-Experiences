export type RiskLevel = "HIGH" | "MEDIUM" | "LOW" | "SAFE";

export function calculateRisk(score: number): RiskLevel {
  if (score >= 70) return "HIGH";
  if (score >= 40) return "MEDIUM";
  if (score >= 20) return "LOW";
  return "SAFE";
}