"""
SQLAlchemy Models for AEO Tracker

Based on Ethan Smith's 4-step AEO methodology:
1. Questions - Target LLM questions to rank for
2. Visibility Checks - Track brand appearance in LLM responses
3. Content - Track published content across platforms
4. Experiments - A/B test content effectiveness
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    Boolean, ForeignKey, JSON, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class VisibilityStatus(enum.Enum):
    """How the brand appears in LLM responses"""
    FEATURED = "featured"           # Prominently recommended
    MENTIONED = "mentioned"         # Mentioned positively
    LISTED = "listed"               # Appears in a list
    CITED_SOURCE = "cited_source"   # Content cited as source
    NOT_FOUND = "not_found"         # Doesn't appear


class ExperimentStatus(enum.Enum):
    """Status of an A/B experiment"""
    DRAFT = "draft"
    CONTROL_PERIOD = "control_period"
    TEST_PERIOD = "test_period"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Brand(Base):
    """
    Brand/Product being tracked for AEO visibility
    """
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    domain = Column(String(255))  # e.g., "webflow.com"
    description = Column(Text)
    keywords = Column(JSON)  # List of brand-related keywords to detect
    competitors = Column(JSON)  # List of competitor names
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    questions = relationship("Question", back_populates="brand", cascade="all, delete-orphan")
    contents = relationship("Content", back_populates="brand", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="brand", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Brand(name='{self.name}')>"


class Question(Base):
    """
    Target LLM questions to track visibility for.

    Step 1: Convert paid keywords to natural questions
    Example: "website builder for designers" ->
             "What's the best website builder for a freelance designer?"
    """
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)

    # Original keyword that inspired the question
    source_keyword = Column(String(255))

    # The actual question to ask LLMs
    question_text = Column(Text, nullable=False)

    # Categorization
    category = Column(String(100))  # e.g., "product comparison", "how-to", "best for"
    intent = Column(String(100))    # e.g., "purchase", "research", "learn"

    # Priority for tracking
    priority = Column(Integer, default=5)  # 1-10 scale
    is_active = Column(Boolean, default=True)

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="questions")
    visibility_checks = relationship("VisibilityCheck", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Question(text='{self.question_text[:50]}...')>"


class Content(Base):
    """
    Track published content across different platforms.

    Step 3: Publish answers where LLMs look
    - YouTube tutorials
    - Reddit answers
    - Landing pages
    - Help center articles
    - etc.
    """
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)

    # Content details
    title = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)  # YouTube, Reddit, Landing Page, etc.
    url = Column(String(1000))
    platform = Column(String(100))  # youtube.com, reddit.com, own website, etc.

    # Content metadata
    description = Column(Text)
    target_keywords = Column(JSON)  # Keywords this content targets

    # Linked questions this content should help rank for
    target_question_ids = Column(JSON)  # List of question IDs

    # Publishing info
    published_at = Column(DateTime)
    is_published = Column(Boolean, default=True)

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="contents")

    def __repr__(self):
        return f"<Content(title='{self.title[:50]}...', type='{self.content_type}')>"


class VisibilityCheck(Base):
    """
    Record of checking brand visibility for a question on an LLM.

    Step 2: Check your current visibility on LLMs
    """
    __tablename__ = "visibility_checks"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=True)

    # Which LLM was queried
    llm_provider = Column(String(50), nullable=False)  # chatgpt, claude, gemini, perplexity
    llm_model = Column(String(100))  # specific model version

    # The response
    response_text = Column(Text)

    # Visibility analysis
    visibility_status = Column(String(50))  # featured, mentioned, listed, cited_source, not_found
    visibility_score = Column(Integer)  # 0-100

    # Position tracking
    position_in_list = Column(Integer)  # If listed, what position (1st, 2nd, etc.)
    total_competitors_mentioned = Column(Integer)

    # Sources cited by the LLM
    cited_sources = Column(JSON)  # List of URLs/sources the LLM mentioned

    # Competitor analysis
    competitors_found = Column(JSON)  # Which competitors appeared in the response

    # Metadata
    checked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    question = relationship("Question", back_populates="visibility_checks")
    experiment = relationship("Experiment", back_populates="visibility_checks")

    def __repr__(self):
        return f"<VisibilityCheck(llm='{self.llm_provider}', status='{self.visibility_status}')>"


class Experiment(Base):
    """
    A/B experiment to test content effectiveness.

    Step 4: Test like a scientist
    - Pick target questions
    - Track control period (2 weeks)
    - Add content intervention
    - Track test period (4 weeks)
    - Compare results
    """
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)

    # Experiment details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    hypothesis = Column(Text)  # What we expect to happen

    # Target questions for this experiment
    target_question_ids = Column(JSON)  # List of question IDs

    # Content intervention
    content_intervention = Column(Text)  # Description of what content was added
    content_ids = Column(JSON)  # List of content IDs added during experiment

    # Timeline
    control_start = Column(DateTime)
    control_end = Column(DateTime)
    test_start = Column(DateTime)
    test_end = Column(DateTime)

    # Status
    status = Column(String(50), default="draft")

    # Results (calculated after experiment)
    control_avg_score = Column(Float)
    test_avg_score = Column(Float)
    score_change = Column(Float)  # Percentage change

    # Statistical significance
    is_significant = Column(Boolean)
    p_value = Column(Float)

    # Conclusions
    conclusion = Column(Text)
    learnings = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="experiments")
    visibility_checks = relationship("VisibilityCheck", back_populates="experiment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Experiment(name='{self.name}', status='{self.status}')>"
