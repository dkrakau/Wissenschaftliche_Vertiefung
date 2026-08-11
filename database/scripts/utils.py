from urllib.parse import urlsplit, urlunsplit


def parse_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""

    max_pos = max(pos for positions in inverted_index.values() for pos in positions)

    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word

    return " ".join(words)


def work_url_to_api_url(work_url: str) -> str:
    parts = urlsplit(work_url)
    parts = parts._replace(netloc="api." + parts.netloc)
    return urlunsplit(parts)
