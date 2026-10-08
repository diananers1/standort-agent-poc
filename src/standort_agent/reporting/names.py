"""Customer-facing district names; source identifiers remain unchanged."""

def format_location_text(text: str) -> str:
    for number, ordinal in [(1, '1st'), (7, '7th'), (10, '10th')]:
        text = text.replace(f'Wien ({number}., ', f'Wien ({ordinal} district, ')
    return text
