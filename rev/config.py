"""Revenue report table and combination configuration."""

REVENUE_TABLES = {
    "1": {"label": "Ticket Sales", "required": True},
    "2": {"label": "Direct State or Other"},
    "3": {"label": "Student Fees"},
    "4": {"label": "Direct Institutional"},
    "7": {"label": "Guarantees"},
    "8": {"label": "Contributions"},
    "11": {"label": "Media Rights"},
    "12": {"label": "NCAA Distributions"},
    "13": {"label": "Conference Distributions"},
    "13A": {"label": "Conference Distributions of Football Bowl Generated Revenue"},
    "14": {"label": "Program, Novelty, Parking and Concession Sales"},
    "15": {"label": "Royalties, Licensing, Advertisement and Sponsorships"},
    "18": {"label": "Other Operating"},
    "19": {"label": "Football Bowl"},
}

REVENUE_TABLE_LABELS = {
    table_id: config["label"]
    for table_id, config in REVENUE_TABLES.items()
}

REVENUE_COMBINATIONS = {
    "2": ["2", "4"],
    "12": ["12", "13"],
    "16": ["13A", "19"],
}

REVENUE_COMBINATION_DESCRIPTIONS = {
    target: f"{target} = " + " + ".join(sources)
    for target, sources in REVENUE_COMBINATIONS.items()
}

EXPECTED_REVENUE_TABLE_IDS = list(REVENUE_TABLES.keys())


def revenue_table_label(table_id: str) -> str:
    return REVENUE_TABLE_LABELS.get(table_id, table_id)
