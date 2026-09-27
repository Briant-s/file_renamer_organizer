from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from ollama import chat


class FileMetaData(BaseModel):
    topic: str
    date: str | None = None  # YYYY-MM-DD if found in content, else None


def _resolve_date(ai_date: str | None, created_at: datetime | None) -> str:
    """
    Priority:
    1. Date extracted from content by the LLM
    2. File creation date from filesystem
    3. Today's date as last resort
    """
    if ai_date:
        return ai_date
    if created_at:
        return created_at.strftime("%Y-%m-%d")
    return datetime.now().strftime("%Y-%m-%d")


def generate_name(
    extracted_text: str,
    original_file: str,
    formatter: callable,
    created_at: datetime | None = None,
    use_date: bool = False,
) -> str:
    suffix = Path(original_file).suffix
    truncated = " ".join(extracted_text.split())[:1000] if extracted_text else ""

    date_instruction = (
        "- If the content mentions a specific date (e.g. invoice date, report date, meeting date), "
        "extract it as YYYY-MM-DD and return it in the date field. Otherwise return null.\n"
        if use_date else
        "- Set date to null.\n"
    )

    prompt = (
        f"Read the file content below and return a short descriptive title (2-4 words) "
        f"that describes what the file is about.\n\n"
        f"Rules:\n"
        f"- Return only the title words, no extension, no punctuation, no explanation\n"
        f"- Be specific, not generic (e.g. 'Grocery Shopping List' not 'Text Document')\n"
        f"{date_instruction}"
        f"\nContent:\n{truncated}"
    )

    result = chat(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": prompt}],
        format=FileMetaData.model_json_schema(),
        options={"temperature": 0}
    )

    ai_response = FileMetaData.model_validate_json(result.message.content)
    formatted = formatter(ai_response.topic)

    if use_date:
        date_str = _resolve_date(ai_response.date, created_at)
        return f"{date_str} {formatted}{suffix}"

    return f"{formatted}{suffix}"


if __name__ == "__main__":
    import re
    from datetime import datetime

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
            "content": """
                Invoice Date: 2024-03-15
                Client: Acme Corp
                Services: Web development, UI design
                Total Due: $3,200
            """
        },
        {
            "file": "notes.txt",
            "format": "snake_case",
            "use_date": True,
            "created_at": datetime(2026, 9, 8),
            "content": """
                Meeting notes - product sync
                Attendees: Brian, Jess, Tom
                - Finalize onboarding flow by Friday
                - API rate limiting needs review
            """
        },
        {
            "file": "report.pdf",
            "format": "Title Case",
            "use_date": False,
            "created_at": None,
            "content": """
                Q3 Financial Summary
                Total Revenue: $1,250,000
                Net Profit: $410,000
            """
        },
    ]

    for case in test_cases:
        formatter = formatters[case["format"]]
        print(f"\nOriginal  : {case['file']}")
        print(f"Format    : {case['format']}")
        print(f"Use date  : {case['use_date']}")
        result = generate_name(
            extracted_text=case["content"],
            original_file=case["file"],
            formatter=formatter,
            created_at=case["created_at"],
            use_date=case["use_date"],
        )
        print(f"Result    : {result}")
        print("-" * 40)
