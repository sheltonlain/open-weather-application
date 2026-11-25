"""Pure helper that decides whether a search query is a city or a ZIP code."""

from dataclasses import dataclass

DEFAULT_COUNTRY = "US"


@dataclass(frozen=True)
class ParsedQuery:
    """A search query classified as "city" or "zip"."""

    kind: str
    value: str


def parse_query(raw: str) -> ParsedQuery:
    """Classify a search box query as a city name or a ZIP/postal code.

    Input starting with a digit is a ZIP (country defaults to US). A postcode
    that starts with a letter (e.g. UK "SW1A 1AA") counts as a ZIP only when a
    two-letter country code follows a comma. Everything else is a city.
    """
    text = raw.strip()
    code, _, country = (part.strip() for part in text.rpartition(","))
    if not code:
        # No comma: rpartition puts the whole text in the last part.
        code, country = country, ""

    has_country = len(country) == 2 and country.isalpha()
    starts_with_digit = code[:1].isdigit()
    letter_first_postcode = has_country and any(ch.isdigit() for ch in code)

    if starts_with_digit or letter_first_postcode:
        country = country.upper() if has_country else DEFAULT_COUNTRY
        return ParsedQuery("zip", f"{code},{country}")
    return ParsedQuery("city", text)
