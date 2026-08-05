import re

SUSPICIOUS_KEYWORDS = [
    "urgent", "verify", "immediately", "suspend",
    "click here", "limited time", "password", "bank"
]

def extract_features(email):
    body = email.body.lower()
    subject = email.subject.lower()

    return {
        "num_links": len(email.links),
        "urgent_language": any(word in body for word in SUSPICIOUS_KEYWORDS),
        "spoofed_domain": not email.sender.endswith("@trustedcompany.com"),
        "contains_html_form": "<form" in body,
        # detect plain-IP URLs in either the message body or the links list
        "has_ip_link": (
            bool(re.search(r"http[s]?://\d+\.\d+\.\d+\.\d+", body))
            or any(re.search(r"http[s]?://\d+\.\d+\.\d+\.\d+", link) for link in email.links)
        ),
    }