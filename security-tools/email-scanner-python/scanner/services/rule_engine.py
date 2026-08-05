def apply_rules(features):
    score = 0
    flags = []

    if features["num_links"] > 2:
        score += 15
        flags.append("multiple_links")

    if features["urgent_language"]:
        score += 20
        flags.append("urgent_language")

    if features["spoofed_domain"]:
        score += 25
        flags.append("suspicious_sender")

    if features["contains_html_form"]:
        score += 20
        flags.append("html_form")

    if features["has_ip_link"]:
        score += 30
        flags.append("ip_address_link")

    return score, flags