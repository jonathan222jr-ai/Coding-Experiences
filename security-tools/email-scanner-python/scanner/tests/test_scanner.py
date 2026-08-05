# imports should reference the package namespace
from scanner.models.email_model import EmailModel
from scanner.services.scanner_engine import scan_email

def test_high_risk_email():
    email = EmailModel(
        subject="URGENT: Verify your bank account",
        sender="attacker@fakebank.com",
        body="Click here immediately to verify your password.",
        links=["http://192.168.1.1/login"]
    )

    result = scan_email(email)
    assert result["risk_level"] == "HIGH"

def test_example_phishing_email():
    # Body copied from user's sample; treat the visible URL as a link
    body = (
        "Dear Customer,\n\n"
        "We detected a suspicious login attempt on your account from an unrecognized device located in Eastern Europe on February 27, 2026 at 3:42 AM.\n\n"
        "If this was not you, your account may be at risk of permanent suspension within the next 24 hours.\n\n"
        "To secure your account immediately, please verify your identity by clicking the secure link below:\n\n"
        " Verify My Account Now\n"
        "www.passwordstealer.com\n\n"
        "Failure to verify your account will result in:\n\n"
        "Immediate account lock\n\n"
        "Loss of stored files and emails\n\n"
        "Permanent data deletion\n\n"
        "For your protection, this link will expire within 12 hours.\n\n"
        "Thank you for your prompt attention.\n\n"
        "Sincerely,\n"
        "Account Protection Team\n"
        "Microsoft Security Department"
    )

    email = EmailModel(
        subject="Suspicious login detected",
        sender="security@fake-microsoft.com",
        body=body,
        links=["http://www.passwordstealer.com"]
    )

    result = scan_email(email)
    # expected to trigger medium risk with the current scoring rules
    assert result["risk_level"] == "MEDIUM"
    print("example email scan:", result)
