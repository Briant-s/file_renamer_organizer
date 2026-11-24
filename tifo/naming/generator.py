"""Backward-compatible naming entry point.

The naming logic now lives in a strategy router (see router.py / strategies.py /
name_request.py). This module keeps the original `generate_name(...)` function
signature so existing callers and tests keep working, while delegating to the
router. New code can use `tifo.naming.router.default_router` directly.
"""

from datetime import datetime

from tifo.naming.name_request import NameRequest
from tifo.naming.router import default_router

# Re-exported for any code importing these from here historically.
from tifo.naming.strategies import FileMetaData, IMAGE_SUFFIXES  # noqa: F401
from tifo.naming.name_request import clean_stem as _clean_stem  # noqa: F401
from tifo.naming.name_request import resolve_date as _resolve_date  # noqa: F401


def generate_name(
    extracted_text: str,
    original_file: str,
    formatter: callable,
    created_at: datetime | None = None,
    use_date: bool = False,
    file_type: str | None = None,
    metadata: dict | None = None,
) -> str:
    """Generate a file name by routing to the appropriate naming strategy.

    Thin wrapper: builds a NameRequest and hands it to the router. Kept for
    backward compatibility with the original positional signature.
    """
    req = NameRequest(
        original_file=original_file,
        formatter=formatter,
        content=extracted_text,
        file_type=file_type,
        created_at=created_at,
        use_date=use_date,
        metadata=metadata or {},
    )
    return default_router.name(req)


if __name__ == "__main__":
    import re

    formatters = {
        "Title Case": lambda s: s.title(),
        "snake_case": lambda s: re.sub(r"\s+", "_", s.strip().lower()),
        "kebab-case": lambda s: re.sub(r"\s+", "-", s.strip().lower()),
    }

    test_cases = [
        {
            "file": "invoice.pdf",
            "format": "Title Case",
            "use_date": True,
            "created_at": datetime(2024, 3, 15),
            "content": "Invoice Date: 2024-03-15\nClient: Acme Corp\nTotal Due: $3,200",
        },
        {
            "file": "report.pdf",
            "format": "Title Case",
            "use_date": False,
            "created_at": None,
            "content": "Q3 Financial Summary\nTotal Revenue: $1,250,000\nNet Profit: $410,000",
        },
        {
            "file": "DSC_4115.acr_.jpeg",
            "format": "Title Case",
            "use_date": False,
            "created_at": None,
            "content": None,
            "file_type": ".jpeg",
            "metadata": {"device": "NIKON CORPORATION NIKON Z 8",
                         "dimensions": {"width": 8256, "height": 5504}},
        },
    ]

    for case in test_cases:
        formatter = formatters[case["format"]]
        result = generate_name(
            extracted_text=case.get("content"),
            original_file=case["file"],
            formatter=formatter,
            created_at=case.get("created_at"),
            use_date=case["use_date"],
            file_type=case.get("file_type"),
            metadata=case.get("metadata"),
        )
        print(f"{case['file']:<24} -> {result}")
