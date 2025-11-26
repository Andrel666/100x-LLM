"""
Visibility Analyzer for AEO Tracker.

Analyzes LLM responses to determine brand visibility and extract insights.
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from ..config import VISIBILITY_SCORES
from ..database.models import Brand, Question, VisibilityCheck
from ..database.db import get_db
from .llm_service import LLMService, LLMResponse


@dataclass
class VisibilityResult:
    """Result of visibility analysis for a single LLM response"""
    brand_name: str
    llm_provider: str
    llm_model: str
    question: str
    response_text: str

    # Visibility metrics
    visibility_status: str  # featured, mentioned, listed, cited_source, not_found
    visibility_score: int   # 0-100

    # Position tracking
    position_in_list: Optional[int] = None
    total_items_in_list: Optional[int] = None

    # Sources and competitors
    cited_sources: List[str] = field(default_factory=list)
    competitors_found: List[str] = field(default_factory=list)

    # Context
    mention_context: str = ""  # The sentence/paragraph where brand was mentioned


class VisibilityAnalyzer:
    """
    Analyzes LLM responses to determine brand visibility.

    Key functions:
    1. Check if brand appears in response
    2. Determine visibility status (featured, mentioned, listed, etc.)
    3. Extract position in lists
    4. Find cited sources
    5. Identify competitor mentions
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()

    def analyze_response(
        self,
        response_text: str,
        brand_name: str,
        brand_keywords: List[str],
        competitors: List[str],
        llm_provider: str = "",
        llm_model: str = "",
        question: str = ""
    ) -> VisibilityResult:
        """
        Analyze a single LLM response for brand visibility.

        Args:
            response_text: The LLM's response
            brand_name: Name of the brand to look for
            brand_keywords: Additional keywords/variations of brand name
            competitors: List of competitor names to track
            llm_provider: Which LLM generated this response
            llm_model: Specific model used
            question: The question that was asked

        Returns:
            VisibilityResult with analysis
        """
        response_lower = response_text.lower()

        # All brand terms to search for
        brand_terms = [brand_name.lower()] + [k.lower() for k in brand_keywords]

        # Check if brand appears
        brand_found = any(term in response_lower for term in brand_terms)

        # Determine visibility status and extract context
        if brand_found:
            visibility_status, position, total, context = self._analyze_mention_type(
                response_text, brand_terms
            )
        else:
            visibility_status = "not_found"
            position = None
            total = None
            context = ""

        # Get score
        visibility_score = VISIBILITY_SCORES.get(visibility_status, 0)

        # Extract cited sources (URLs)
        cited_sources = self._extract_urls(response_text)

        # Find competitors
        competitors_found = self._find_competitors(response_text, competitors)

        return VisibilityResult(
            brand_name=brand_name,
            llm_provider=llm_provider,
            llm_model=llm_model,
            question=question,
            response_text=response_text,
            visibility_status=visibility_status,
            visibility_score=visibility_score,
            position_in_list=position,
            total_items_in_list=total,
            cited_sources=cited_sources,
            competitors_found=competitors_found,
            mention_context=context
        )

    def _analyze_mention_type(
        self,
        response_text: str,
        brand_terms: List[str]
    ) -> Tuple[str, Optional[int], Optional[int], str]:
        """
        Determine how the brand is mentioned in the response.

        Returns: (status, position_in_list, total_in_list, mention_context)
        """
        response_lower = response_text.lower()

        # Check for featured/recommended patterns
        featured_patterns = [
            r"(?:i |we )?(?:recommend|suggest)\s+(?:using\s+)?",
            r"(?:the )?best (?:option|choice|tool|solution) is\s+",
            r"(?:my |our )?top (?:pick|choice|recommendation) is\s+",
            r"(?:you should |i\'d |we\'d )?(?:go with|choose|use)\s+",
        ]

        for pattern in featured_patterns:
            for term in brand_terms:
                if re.search(pattern + re.escape(term), response_lower):
                    context = self._extract_context(response_text, term)
                    return ("featured", 1, None, context)

        # Check for numbered list position
        list_pattern = r"(?:^|\n)\s*(\d+)[.):]\s*\*?\*?([^\n]+)"
        matches = re.findall(list_pattern, response_text, re.MULTILINE)

        if matches:
            for idx, (num, item) in enumerate(matches):
                item_lower = item.lower()
                if any(term in item_lower for term in brand_terms):
                    context = item.strip()
                    return ("listed", int(num), len(matches), context)

        # Check for bullet point lists
        bullet_pattern = r"(?:^|\n)\s*[-*•]\s*\*?\*?([^\n]+)"
        bullet_matches = re.findall(bullet_pattern, response_text, re.MULTILINE)

        if bullet_matches:
            for idx, item in enumerate(bullet_matches):
                item_lower = item.lower()
                if any(term in item_lower for term in brand_terms):
                    context = item.strip()
                    return ("listed", idx + 1, len(bullet_matches), context)

        # Check if brand's content is cited as a source
        source_patterns = [
            r"according to\s+" + "|".join(re.escape(t) for t in brand_terms),
            r"source[sd]?:\s*.*" + "|".join(re.escape(t) for t in brand_terms),
            r"from\s+" + "|".join(re.escape(t) for t in brand_terms) + r"['\"]?s?\s+(?:website|blog|article|documentation)",
        ]

        for pattern in source_patterns:
            if re.search(pattern, response_lower):
                context = self._extract_context(response_text, brand_terms[0])
                return ("cited_source", None, None, context)

        # Default to mentioned (brand found but not in special context)
        context = self._extract_context(response_text, brand_terms[0])
        return ("mentioned", None, None, context)

    def _extract_context(self, text: str, term: str, context_chars: int = 200) -> str:
        """Extract surrounding context for a term mention"""
        text_lower = text.lower()
        term_lower = term.lower()

        pos = text_lower.find(term_lower)
        if pos == -1:
            return ""

        start = max(0, pos - context_chars // 2)
        end = min(len(text), pos + len(term) + context_chars // 2)

        context = text[start:end].strip()
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context

    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://[^\s<>"\')\]]+|www\.[^\s<>"\')\]]+'
        urls = re.findall(url_pattern, text)
        return list(set(urls))  # Remove duplicates

    def _find_competitors(self, text: str, competitors: List[str]) -> List[str]:
        """Find which competitors are mentioned in the text"""
        text_lower = text.lower()
        found = []
        for competitor in competitors:
            if competitor.lower() in text_lower:
                found.append(competitor)
        return found

    def check_visibility(
        self,
        brand: Brand,
        question: Question,
        llm_keys: List[str] = None
    ) -> List[VisibilityResult]:
        """
        Check brand visibility for a question across specified LLMs.

        Args:
            brand: Brand to check visibility for
            question: Question to ask LLMs
            llm_keys: List of LLM keys to query (default: all available)

        Returns:
            List of VisibilityResult for each LLM
        """
        if llm_keys is None:
            llm_keys = [p["key"] for p in self.llm_service.get_available_providers()]

        results = []
        brand_keywords = brand.keywords or []
        competitors = brand.competitors or []

        for llm_key in llm_keys:
            # Query the LLM
            response = self.llm_service.query(llm_key, question.question_text)

            if response.success:
                # Analyze the response
                result = self.analyze_response(
                    response_text=response.response_text,
                    brand_name=brand.name,
                    brand_keywords=brand_keywords,
                    competitors=competitors,
                    llm_provider=response.provider,
                    llm_model=response.model,
                    question=question.question_text
                )
                results.append(result)

        return results

    def save_visibility_check(
        self,
        result: VisibilityResult,
        question_id: int,
        experiment_id: Optional[int] = None
    ) -> VisibilityCheck:
        """Save a visibility check result to the database"""
        with get_db() as db:
            check = VisibilityCheck(
                question_id=question_id,
                experiment_id=experiment_id,
                llm_provider=result.llm_provider,
                llm_model=result.llm_model,
                response_text=result.response_text,
                visibility_status=result.visibility_status,
                visibility_score=result.visibility_score,
                position_in_list=result.position_in_list,
                total_competitors_mentioned=len(result.competitors_found),
                cited_sources=result.cited_sources,
                competitors_found=result.competitors_found,
                checked_at=datetime.utcnow()
            )
            db.add(check)
            db.commit()
            db.refresh(check)
            return check

    def get_visibility_summary(self, brand_id: int, days: int = 30) -> Dict:
        """
        Get a summary of visibility checks for a brand over time.

        Returns aggregated metrics like:
        - Average visibility score per LLM
        - Visibility trend over time
        - Most common competitors
        """
        from datetime import timedelta

        with get_db() as db:
            cutoff = datetime.utcnow() - timedelta(days=days)

            checks = db.query(VisibilityCheck).join(Question).filter(
                Question.brand_id == brand_id,
                VisibilityCheck.checked_at >= cutoff
            ).all()

            if not checks:
                return {"total_checks": 0, "message": "No visibility data found"}

            # Aggregate by provider
            by_provider = {}
            for check in checks:
                if check.llm_provider not in by_provider:
                    by_provider[check.llm_provider] = {
                        "scores": [],
                        "statuses": []
                    }
                by_provider[check.llm_provider]["scores"].append(check.visibility_score or 0)
                by_provider[check.llm_provider]["statuses"].append(check.visibility_status)

            # Calculate averages
            summary = {
                "total_checks": len(checks),
                "by_provider": {},
                "overall_avg_score": sum(c.visibility_score or 0 for c in checks) / len(checks)
            }

            for provider, data in by_provider.items():
                summary["by_provider"][provider] = {
                    "avg_score": sum(data["scores"]) / len(data["scores"]),
                    "check_count": len(data["scores"]),
                    "featured_count": data["statuses"].count("featured"),
                    "mentioned_count": data["statuses"].count("mentioned"),
                    "not_found_count": data["statuses"].count("not_found")
                }

            return summary
