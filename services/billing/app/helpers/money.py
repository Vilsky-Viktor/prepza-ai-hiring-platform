def row_minor(row) -> int | None:
    """What a loaded `Entry` or `Purchase` moved, in minor units: the integer column, or the old
    text one for a row an older version wrote during a deploy (migration 0020). The fallback goes
    with the text column."""
    if row.total_minor is not None:
        return row.total_minor

    return int(row.total) if row.total is not None else None
