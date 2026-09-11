import re


def parse_journey_message(message):
    """
    Extract origin, destination and optional route from
    common natural-language journey questions.
    """

    text = str(message).strip()

    patterns = [
        r"from\s+(.+?)\s+to\s+(.+?)(?:\?|$)",
        r"between\s+(.+?)\s+and\s+(.+?)(?:\?|$)",
    ]

    origin = None
    destination = None

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            break

    route = None

    route_match = re.search(
        r"\b(?:route|bus)\s*([A-Z]?\d+[A-Z]?)\b",
        text,
        flags=re.IGNORECASE
    )

    if route_match:
        route = route_match.group(1).upper()

    return {
        "origin": origin,
        "destination": destination,
        "route": route,
    }
