# Email Scanner (Python)

The scanning engine behind the [`fraud-email-scanner`](../../office-addins/fraud-email-scanner)
Outlook add-in, implemented in Python and covered by unit tests.

The design mirrors the TypeScript version so the two can be compared side by side:

| Module | Role |
|---|---|
| `scanner/models/email_model.py` | Normalized representation of a message |
| `scanner/services/feature_extractor.py` | Pulls signals (sender, links, headers, body cues) out of a message |
| `scanner/services/rule_engine.py` | Evaluates the extracted features against detection rules |
| `scanner/services/risk_scorer.py` | Combines rule hits into a single risk score |
| `scanner/services/scanner_engine.py` | Orchestrates extract → evaluate → score |

## Running the tests

```bash
python -m pytest scanner/tests
```

Test fixtures use synthetic addresses (`attacker@fakebank.com` and similar) — no real
message data is included.
