"""Utility functions for formatting output."""


def format_currency(value: float) -> str:
    """Format a number as currency."""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format a number as percentage."""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def format_table(headers: list[str], rows: list[list[str]], min_width: int = 12) -> str:
    """Format data as an aligned text table."""
    col_widths = [max(min_width, len(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    def format_row(cells: list[str]) -> str:
        parts = []
        for i, cell in enumerate(cells):
            width = col_widths[i] if i < len(col_widths) else min_width
            parts.append(str(cell).rjust(width))
        return "  ".join(parts)

    lines = [
        format_row(headers),
        "  ".join("-" * w for w in col_widths),
    ]
    for row in rows:
        lines.append(format_row(row))

    return "\n".join(lines)
