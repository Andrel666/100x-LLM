"""
Experiment Manager for AEO Tracker.

Implements Ethan Smith's Step 4: Test like a scientist

Experiment workflow:
1. Define hypothesis and target questions
2. Run control period (2 weeks) - measure baseline visibility
3. Implement content intervention
4. Run test period (4 weeks) - measure new visibility
5. Analyze results and determine significance
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from ..config import DEFAULT_CONTROL_PERIOD_DAYS, DEFAULT_TEST_PERIOD_DAYS
from ..database.models import Brand, Question, Experiment, VisibilityCheck
from ..database.db import get_db
from .visibility import VisibilityAnalyzer


@dataclass
class ExperimentResults:
    """Results from an A/B experiment"""
    experiment_id: int
    experiment_name: str

    # Control period metrics
    control_checks: int
    control_avg_score: float
    control_featured_rate: float

    # Test period metrics
    test_checks: int
    test_avg_score: float
    test_featured_rate: float

    # Comparison
    score_change: float  # Percentage change
    score_change_absolute: float
    featured_rate_change: float

    # Statistical analysis
    is_significant: bool
    p_value: Optional[float]
    confidence_level: str  # "high", "medium", "low", "insufficient_data"

    # By provider breakdown
    by_provider: Dict[str, Dict]


class ExperimentManager:
    """
    Manages A/B experiments for testing AEO content effectiveness.

    Usage:
        manager = ExperimentManager()

        # Create experiment
        exp = manager.create_experiment(
            brand_id=1,
            name="YouTube Tutorial Test",
            hypothesis="Adding YouTube tutorials will increase visibility",
            target_question_ids=[1, 2, 3]
        )

        # Start control period
        manager.start_control_period(exp.id)

        # ... wait 2 weeks, run visibility checks ...

        # Start test period (after adding content)
        manager.start_test_period(exp.id)

        # ... wait 4 weeks, run visibility checks ...

        # Analyze results
        results = manager.analyze_experiment(exp.id)
    """

    def __init__(self, visibility_analyzer: Optional[VisibilityAnalyzer] = None):
        self.visibility_analyzer = visibility_analyzer or VisibilityAnalyzer()

    def create_experiment(
        self,
        brand_id: int,
        name: str,
        hypothesis: str,
        target_question_ids: List[int],
        description: str = "",
        control_days: int = DEFAULT_CONTROL_PERIOD_DAYS,
        test_days: int = DEFAULT_TEST_PERIOD_DAYS
    ) -> Experiment:
        """
        Create a new A/B experiment.

        Args:
            brand_id: ID of the brand being tested
            name: Name of the experiment
            hypothesis: What you expect to happen
            target_question_ids: Questions to track during experiment
            description: Detailed description
            control_days: Length of control period in days
            test_days: Length of test period in days
        """
        with get_db() as db:
            experiment = Experiment(
                brand_id=brand_id,
                name=name,
                description=description,
                hypothesis=hypothesis,
                target_question_ids=target_question_ids,
                status="draft"
            )
            db.add(experiment)
            db.commit()
            db.refresh(experiment)
            return experiment

    def start_control_period(self, experiment_id: int) -> Experiment:
        """Start the control period for an experiment"""
        with get_db() as db:
            experiment = db.query(Experiment).filter(
                Experiment.id == experiment_id
            ).first()

            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")

            experiment.status = "control_period"
            experiment.control_start = datetime.utcnow()
            experiment.control_end = datetime.utcnow() + timedelta(
                days=DEFAULT_CONTROL_PERIOD_DAYS
            )

            db.commit()
            db.refresh(experiment)
            return experiment

    def start_test_period(
        self,
        experiment_id: int,
        content_intervention: str,
        content_ids: List[int] = None
    ) -> Experiment:
        """
        Start the test period for an experiment.

        Args:
            experiment_id: ID of the experiment
            content_intervention: Description of what content was added
            content_ids: IDs of content items added (optional)
        """
        with get_db() as db:
            experiment = db.query(Experiment).filter(
                Experiment.id == experiment_id
            ).first()

            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")

            experiment.status = "test_period"
            experiment.content_intervention = content_intervention
            experiment.content_ids = content_ids or []
            experiment.test_start = datetime.utcnow()
            experiment.test_end = datetime.utcnow() + timedelta(
                days=DEFAULT_TEST_PERIOD_DAYS
            )

            db.commit()
            db.refresh(experiment)
            return experiment

    def run_visibility_checks(
        self,
        experiment_id: int,
        llm_keys: List[str] = None
    ) -> List[VisibilityCheck]:
        """
        Run visibility checks for all target questions in an experiment.
        """
        with get_db() as db:
            experiment = db.query(Experiment).filter(
                Experiment.id == experiment_id
            ).first()

            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")

            brand = db.query(Brand).filter(Brand.id == experiment.brand_id).first()
            question_ids = experiment.target_question_ids or []

            questions = db.query(Question).filter(
                Question.id.in_(question_ids)
            ).all()

            checks = []
            for question in questions:
                results = self.visibility_analyzer.check_visibility(
                    brand=brand,
                    question=question,
                    llm_keys=llm_keys
                )

                for result in results:
                    check = self.visibility_analyzer.save_visibility_check(
                        result=result,
                        question_id=question.id,
                        experiment_id=experiment_id
                    )
                    checks.append(check)

            return checks

    def complete_experiment(self, experiment_id: int) -> Experiment:
        """Mark an experiment as completed"""
        with get_db() as db:
            experiment = db.query(Experiment).filter(
                Experiment.id == experiment_id
            ).first()

            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")

            experiment.status = "completed"
            db.commit()
            db.refresh(experiment)
            return experiment

    def analyze_experiment(self, experiment_id: int) -> ExperimentResults:
        """
        Analyze the results of a completed experiment.

        Compares control period visibility to test period visibility.
        """
        with get_db() as db:
            experiment = db.query(Experiment).filter(
                Experiment.id == experiment_id
            ).first()

            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")

            # Get all visibility checks for this experiment
            checks = db.query(VisibilityCheck).filter(
                VisibilityCheck.experiment_id == experiment_id
            ).all()

            if not checks:
                return self._empty_results(experiment)

            # Split into control and test periods
            control_checks = []
            test_checks = []

            for check in checks:
                if experiment.control_start and experiment.control_end:
                    if experiment.control_start <= check.checked_at <= experiment.control_end:
                        control_checks.append(check)
                if experiment.test_start and experiment.test_end:
                    if experiment.test_start <= check.checked_at <= experiment.test_end:
                        test_checks.append(check)

            # Calculate metrics
            control_scores = [c.visibility_score or 0 for c in control_checks]
            test_scores = [c.visibility_score or 0 for c in test_checks]

            control_avg = statistics.mean(control_scores) if control_scores else 0
            test_avg = statistics.mean(test_scores) if test_scores else 0

            control_featured = sum(1 for c in control_checks if c.visibility_status == "featured")
            test_featured = sum(1 for c in test_checks if c.visibility_status == "featured")

            control_featured_rate = control_featured / len(control_checks) if control_checks else 0
            test_featured_rate = test_featured / len(test_checks) if test_checks else 0

            # Calculate changes
            if control_avg > 0:
                score_change = ((test_avg - control_avg) / control_avg) * 100
            else:
                score_change = 100 if test_avg > 0 else 0

            score_change_absolute = test_avg - control_avg
            featured_rate_change = test_featured_rate - control_featured_rate

            # Statistical significance (simplified)
            is_significant, p_value, confidence = self._calculate_significance(
                control_scores, test_scores
            )

            # Breakdown by provider
            by_provider = self._analyze_by_provider(control_checks, test_checks)

            # Update experiment with results
            experiment.control_avg_score = control_avg
            experiment.test_avg_score = test_avg
            experiment.score_change = score_change
            experiment.is_significant = is_significant
            experiment.p_value = p_value
            db.commit()

            return ExperimentResults(
                experiment_id=experiment_id,
                experiment_name=experiment.name,
                control_checks=len(control_checks),
                control_avg_score=control_avg,
                control_featured_rate=control_featured_rate,
                test_checks=len(test_checks),
                test_avg_score=test_avg,
                test_featured_rate=test_featured_rate,
                score_change=score_change,
                score_change_absolute=score_change_absolute,
                featured_rate_change=featured_rate_change,
                is_significant=is_significant,
                p_value=p_value,
                confidence_level=confidence,
                by_provider=by_provider
            )

    def _empty_results(self, experiment: Experiment) -> ExperimentResults:
        """Return empty results when no data available"""
        return ExperimentResults(
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            control_checks=0,
            control_avg_score=0,
            control_featured_rate=0,
            test_checks=0,
            test_avg_score=0,
            test_featured_rate=0,
            score_change=0,
            score_change_absolute=0,
            featured_rate_change=0,
            is_significant=False,
            p_value=None,
            confidence_level="insufficient_data",
            by_provider={}
        )

    def _calculate_significance(
        self,
        control_scores: List[float],
        test_scores: List[float]
    ) -> tuple:
        """
        Calculate statistical significance using a simple t-test approximation.

        Returns: (is_significant, p_value, confidence_level)
        """
        if len(control_scores) < 5 or len(test_scores) < 5:
            return (False, None, "insufficient_data")

        try:
            # Simple significance test
            control_mean = statistics.mean(control_scores)
            test_mean = statistics.mean(test_scores)
            control_std = statistics.stdev(control_scores) if len(control_scores) > 1 else 0
            test_std = statistics.stdev(test_scores) if len(test_scores) > 1 else 0

            # Pooled standard error
            n1, n2 = len(control_scores), len(test_scores)
            if control_std == 0 and test_std == 0:
                # No variance - can't determine significance
                return (False, None, "low")

            pooled_se = ((control_std ** 2 / n1) + (test_std ** 2 / n2)) ** 0.5

            if pooled_se == 0:
                return (False, None, "low")

            # T-statistic
            t_stat = abs(test_mean - control_mean) / pooled_se

            # Simple p-value approximation
            # For a proper implementation, use scipy.stats.ttest_ind
            if t_stat > 2.58:  # ~99% confidence
                return (True, 0.01, "high")
            elif t_stat > 1.96:  # ~95% confidence
                return (True, 0.05, "medium")
            elif t_stat > 1.645:  # ~90% confidence
                return (False, 0.10, "low")
            else:
                return (False, 0.5, "low")

        except Exception:
            return (False, None, "insufficient_data")

    def _analyze_by_provider(
        self,
        control_checks: List[VisibilityCheck],
        test_checks: List[VisibilityCheck]
    ) -> Dict[str, Dict]:
        """Analyze results broken down by LLM provider"""
        providers = set()
        for c in control_checks + test_checks:
            providers.add(c.llm_provider)

        results = {}
        for provider in providers:
            control = [c for c in control_checks if c.llm_provider == provider]
            test = [c for c in test_checks if c.llm_provider == provider]

            control_avg = statistics.mean([c.visibility_score or 0 for c in control]) if control else 0
            test_avg = statistics.mean([c.visibility_score or 0 for c in test]) if test else 0

            results[provider] = {
                "control_avg": control_avg,
                "test_avg": test_avg,
                "change": test_avg - control_avg,
                "control_count": len(control),
                "test_count": len(test)
            }

        return results

    def get_experiment_status(self, experiment_id: int) -> Dict:
        """Get current status of an experiment"""
        with get_db() as db:
            experiment = db.query(Experiment).filter(
                Experiment.id == experiment_id
            ).first()

            if not experiment:
                return {"error": "Experiment not found"}

            now = datetime.utcnow()

            status = {
                "id": experiment.id,
                "name": experiment.name,
                "status": experiment.status,
                "hypothesis": experiment.hypothesis
            }

            if experiment.status == "control_period":
                if experiment.control_end:
                    days_remaining = (experiment.control_end - now).days
                    status["days_remaining"] = max(0, days_remaining)
                    status["message"] = f"Control period: {days_remaining} days remaining"

            elif experiment.status == "test_period":
                if experiment.test_end:
                    days_remaining = (experiment.test_end - now).days
                    status["days_remaining"] = max(0, days_remaining)
                    status["message"] = f"Test period: {days_remaining} days remaining"

            elif experiment.status == "completed":
                status["message"] = "Experiment completed"
                status["score_change"] = experiment.score_change
                status["is_significant"] = experiment.is_significant

            return status
