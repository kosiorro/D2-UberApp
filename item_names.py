"""Clean catalog formatting markers from item names."""

import re


def clean_item_name(name):
    if not name:
        return name
    return re.sub(r"^(?:\s*\[(?:fs|ms|nl)\]\s*)+", "", name, flags=re.IGNORECASE)
