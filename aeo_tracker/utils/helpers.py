"""
Helper utilities for AEO Tracker

Includes:
- Keyword to question conversion (Step 1)
- Question variation generation
- Data export utilities
"""
from typing import List, Dict
import csv
import io
from datetime import datetime


# Question templates for converting keywords to natural questions
QUESTION_TEMPLATES = [
    "What is the best {keyword}?",
    "What are the top {keyword} options?",
    "Which {keyword} should I choose?",
    "What {keyword} do you recommend?",
    "How do I find a good {keyword}?",
    "What's the best {keyword} for {persona}?",
    "Which {keyword} is best for {use_case}?",
    "What are the pros and cons of different {keyword}?",
    "How does {keyword} compare?",
    "What should I look for in a {keyword}?",
]

# Personas for question generation
DEFAULT_PERSONAS = [
    "beginners",
    "small businesses",
    "enterprises",
    "startups",
    "freelancers",
    "developers",
    "designers",
    "marketers",
    "agencies",
    "teams",
]

# Use cases for question generation
DEFAULT_USE_CASES = [
    "getting started",
    "scaling",
    "budget-conscious users",
    "professional use",
    "personal projects",
    "collaboration",
]


def keyword_to_question(
    keyword: str,
    persona: str = None,
    use_case: str = None,
    template_index: int = 0
) -> str:
    """
    Convert a paid search keyword to a natural LLM question.

    Step 1 of Ethan's methodology:
    "website builder for designers" ->
    "What's the best website builder for a freelance designer who wants visual control?"

    Args:
        keyword: The source keyword (e.g., "website builder for designers")
        persona: Target persona (e.g., "freelancers")
        use_case: Specific use case (e.g., "building portfolios")
        template_index: Which template to use (0-9)

    Returns:
        Natural question string
    """
    template = QUESTION_TEMPLATES[template_index % len(QUESTION_TEMPLATES)]

    question = template.format(
        keyword=keyword,
        persona=persona or "users",
        use_case=use_case or "my needs"
    )

    return question


def generate_question_variations(
    keyword: str,
    num_variations: int = 5,
    include_personas: bool = True,
    include_use_cases: bool = True
) -> List[str]:
    """
    Generate multiple question variations from a single keyword.

    Useful for comprehensive visibility tracking.

    Args:
        keyword: Source keyword
        num_variations: How many variations to generate
        include_personas: Include persona-specific questions
        include_use_cases: Include use-case-specific questions

    Returns:
        List of question variations
    """
    questions = []

    # Basic questions
    basic_templates = QUESTION_TEMPLATES[:5]
    for template in basic_templates[:num_variations]:
        q = template.format(keyword=keyword, persona="users", use_case="my needs")
        questions.append(q)

    # Persona variations
    if include_personas and len(questions) < num_variations:
        for persona in DEFAULT_PERSONAS[:3]:
            if len(questions) >= num_variations:
                break
            q = f"What's the best {keyword} for {persona}?"
            questions.append(q)

    # Use case variations
    if include_use_cases and len(questions) < num_variations:
        for use_case in DEFAULT_USE_CASES[:3]:
            if len(questions) >= num_variations:
                break
            q = f"Which {keyword} is best for {use_case}?"
            questions.append(q)

    return questions[:num_variations]


def format_visibility_score(score: int) -> str:
    """
    Format a visibility score with emoji indicator.

    Args:
        score: Visibility score (0-100)

    Returns:
        Formatted string with score and indicator
    """
    if score >= 80:
        indicator = "Excellent"
        color = "green"
    elif score >= 60:
        indicator = "Good"
        color = "blue"
    elif score >= 40:
        indicator = "Moderate"
        color = "yellow"
    elif score >= 20:
        indicator = "Low"
        color = "orange"
    else:
        indicator = "Not Found"
        color = "red"

    return f"{score}/100 ({indicator})"


def format_visibility_status(status: str) -> Dict[str, str]:
    """
    Get display info for a visibility status.

    Returns dict with label and color for UI display.
    """
    status_map = {
        "featured": {"label": "Featured", "color": "green", "icon": "star"},
        "mentioned": {"label": "Mentioned", "color": "blue", "icon": "chat"},
        "listed": {"label": "Listed", "color": "yellow", "icon": "list"},
        "cited_source": {"label": "Cited Source", "color": "purple", "icon": "link"},
        "not_found": {"label": "Not Found", "color": "red", "icon": "x"},
    }
    return status_map.get(status, {"label": status, "color": "gray", "icon": "question"})


def export_to_csv(data: List[Dict], filename: str = None) -> str:
    """
    Export data to CSV format.

    Args:
        data: List of dictionaries to export
        filename: Optional filename (returns string if not provided)

    Returns:
        CSV string or writes to file
    """
    if not data:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    csv_string = output.getvalue()

    if filename:
        with open(filename, 'w', newline='') as f:
            f.write(csv_string)
        return filename

    return csv_string


def calculate_trend(values: List[float], periods: int = 7) -> Dict:
    """
    Calculate trend from a series of values.

    Args:
        values: List of numeric values (oldest first)
        periods: Number of periods to compare

    Returns:
        Dict with trend info (direction, change, etc.)
    """
    if len(values) < 2:
        return {"direction": "stable", "change": 0, "percent_change": 0}

    recent = values[-periods:] if len(values) >= periods else values
    earlier = values[:periods] if len(values) >= periods * 2 else values[:len(values) // 2]

    recent_avg = sum(recent) / len(recent) if recent else 0
    earlier_avg = sum(earlier) / len(earlier) if earlier else 0

    change = recent_avg - earlier_avg
    percent_change = (change / earlier_avg * 100) if earlier_avg != 0 else 0

    if change > 5:
        direction = "up"
    elif change < -5:
        direction = "down"
    else:
        direction = "stable"

    return {
        "direction": direction,
        "change": round(change, 2),
        "percent_change": round(percent_change, 2),
        "recent_avg": round(recent_avg, 2),
        "earlier_avg": round(earlier_avg, 2)
    }


def generate_experiment_name(content_type: str, target: str) -> str:
    """Generate a descriptive experiment name"""
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{content_type} Test - {target} - {timestamp}"
