"""Sport Ops report table configuration."""

SPORTOPS_TABLES = {
    "21": "Guarantees",
    "27": "Recruiting",
    "28": "Team Travel",
    "29": "Sports Equipment, Uniforms and Supplies",
    "30": "Game Expenses",
    "31": "Fund Raising, Marketing and Promotion",
    "35": "Direct Overhead and Administrative Expenses",
    "36": "Indirect Institutional Support",
    "37": "Medical Expenses and Insurance",
    "38": "Memberships and Dues",
    "39": "Student-Athlete Meals (nontravel)",
    "40": "Other Operating Expenses",
}


def default_sportops_tables() -> dict[str, str]:
    return dict(SPORTOPS_TABLES)


def default_sportops_table_ids() -> list[str]:
    return list(SPORTOPS_TABLES)


def clean_sportops_table_map(table_map, fallback=None) -> dict[str, str]:
    fallback = fallback or SPORTOPS_TABLES
    if not isinstance(table_map, dict):
        return dict(fallback)

    cleaned = {}
    for table_id, label in table_map.items():
        table_id = str(table_id).strip()
        label = str(label).strip()
        if not table_id or not label:
            continue
        if table_id in cleaned:
            continue
        cleaned[table_id] = label
    return cleaned or dict(fallback)


def clean_sportops_table_ids(table_ids, table_map=None) -> list[str]:
    table_map = clean_sportops_table_map(table_map or SPORTOPS_TABLES)
    if isinstance(table_ids, str):
        table_ids = [table_ids]
    if not isinstance(table_ids, list):
        return list(table_map)

    clean_ids = []
    seen = set()
    for table_id in table_ids:
        table_id = str(table_id).strip()
        if table_id not in table_map or table_id in seen:
            continue
        seen.add(table_id)
        clean_ids.append(table_id)

    return clean_ids or list(table_map)


def sportops_table_names(table_ids=None, table_map=None) -> list[str]:
    table_map = clean_sportops_table_map(table_map or SPORTOPS_TABLES)
    return [
        f"{table_id} {table_map[table_id]}"
        for table_id in clean_sportops_table_ids(table_ids or list(table_map), table_map)
    ]


def sportops_table_labels(table_ids=None, table_map=None) -> list[str]:
    table_map = clean_sportops_table_map(table_map or SPORTOPS_TABLES)
    return [
        table_map[table_id]
        for table_id in clean_sportops_table_ids(table_ids or list(table_map), table_map)
    ]


SPORTOPS_TABLE_NUMS = default_sportops_table_ids()
SPORTOPS_TABLE_NAMES = sportops_table_names()
