# Fraud Email Scanner

An Outlook add-in that inspects the open message and flags signs of fraud or phishing,
surfacing a risk assessment in the task pane.

## Stack

TypeScript · Office.js · Webpack · Babel

## Design

The scanner is deliberately split into layers so each stage can be reasoned about and
tested on its own:

| Module | Role |
|---|---|
| `src/scanner/models/EmailModel.ts` | Normalized representation of a message |
| `src/scanner/services/featureExtractor.ts` | Pulls signals out of a message — sender, links, headers, body cues |
| `src/scanner/services/ruleEngine.ts` | Evaluates those features against detection rules |
| `src/scanner/services/riskScorer.ts` | Combines rule hits into a single score |
| `src/scanner/services/scannerEngine.ts` | Orchestrates extract → evaluate → score |
| `src/taskpane/` | The UI that presents the result |

Keeping extraction separate from rules means a new detection is usually a rule change,
not a rewrite.

A Python implementation of the same engine, with unit tests, is in
[`security-tools/email-scanner-python`](../../security-tools/email-scanner-python).

## Running it

```bash
npm install
npm start
```

`manifest.xml` defines the add-in for sideloading into Outlook.
