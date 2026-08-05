# use relative imports now that scanner is a package
from .feature_extractor import extract_features
from .rule_engine import apply_rules
from .risk_scorer import calculate_risk

def scan_email(email):
    features = extract_features(email)
    score, flags = apply_rules(features)
    risk_level = calculate_risk(score)

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "flags": flags,
        "feature_summary": features
    }