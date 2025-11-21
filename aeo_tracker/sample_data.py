"""
Sample Data Loader for AEO Tracker

Run this script to populate the database with example data for testing.

Usage:
    python sample_data.py
"""
from datetime import datetime, timedelta

# Initialize database
from database.db import init_db, get_db
from database.models import Brand, Question, Content

# Sample brand data based on Ethan's example
SAMPLE_BRANDS = [
    {
        "name": "Your360 AI",
        "domain": "your360.ai",
        "description": "A tool for teams to get anonymous feedback from colleagues",
        "keywords": ["Your360", "your360.ai", "Your360 AI", "360 feedback tool"],
        "competitors": ["Culture Amp", "15Five", "Lattice", "Officevibe", "TINYpulse"]
    },
    {
        "name": "Webflow",
        "domain": "webflow.com",
        "description": "Visual web development platform for designers",
        "keywords": ["Webflow", "webflow.com", "Webflow Designer"],
        "competitors": ["Wix", "Squarespace", "WordPress", "Framer", "Carrd"]
    }
]

# Sample questions for Your360 AI
YOUR360_QUESTIONS = [
    {
        "source_keyword": "anonymous feedback tool",
        "question_text": "What's the best tool for getting anonymous feedback from my team?",
        "category": "product comparison"
    },
    {
        "source_keyword": "360 review software",
        "question_text": "Which 360 review software is best for small teams?",
        "category": "product comparison"
    },
    {
        "source_keyword": "team feedback",
        "question_text": "How can I get honest feedback from my team without making it awkward?",
        "category": "how-to"
    },
    {
        "source_keyword": "anonymous employee feedback",
        "question_text": "What are the best ways to collect anonymous employee feedback?",
        "category": "how-to"
    },
    {
        "source_keyword": "360 feedback for startups",
        "question_text": "What 360 feedback tools work best for startups?",
        "category": "best for"
    }
]

# Sample questions for Webflow
WEBFLOW_QUESTIONS = [
    {
        "source_keyword": "website builder for designers",
        "question_text": "What's the best website builder for a freelance designer who wants visual control and doesn't code?",
        "category": "best for"
    },
    {
        "source_keyword": "no-code website builder",
        "question_text": "What are the best no-code website builders for creating professional sites?",
        "category": "product comparison"
    },
    {
        "source_keyword": "webflow vs squarespace",
        "question_text": "How does Webflow compare to Squarespace for building custom websites?",
        "category": "product comparison"
    },
    {
        "source_keyword": "visual web design tool",
        "question_text": "Which visual web design tools give you the most design freedom?",
        "category": "product comparison"
    },
    {
        "source_keyword": "website builder for agencies",
        "question_text": "What website builder do design agencies recommend for client projects?",
        "category": "best for"
    }
]

# Sample content (following Ethan's playbook)
YOUR360_CONTENT = [
    {
        "title": "How to Give Hard Feedback to Your Team",
        "content_type": "YouTube Video",
        "url": "https://youtube.com/watch?v=example1",
        "platform": "youtube.com",
        "description": "A guide on delivering difficult feedback constructively"
    },
    {
        "title": "The Art of Receiving Feedback Without Getting Defensive",
        "content_type": "YouTube Video",
        "url": "https://youtube.com/watch?v=example2",
        "platform": "youtube.com",
        "description": "Tips for managers on how to receive criticism"
    },
    {
        "title": "How do you collect anonymous feedback from your team?",
        "content_type": "Reddit Answer",
        "url": "https://reddit.com/r/management/comments/example",
        "platform": "reddit.com",
        "description": "Answer in r/management discussing feedback tools"
    },
    {
        "title": "Your360 + Slack Integration",
        "content_type": "Integration Page",
        "url": "https://your360.ai/integrations/slack",
        "platform": "your360.ai",
        "description": "How to integrate Your360 with Slack"
    },
    {
        "title": "Anonymous Feedback for Remote Teams",
        "content_type": "Use Case Page",
        "url": "https://your360.ai/use-cases/remote-teams",
        "platform": "your360.ai",
        "description": "Use case page for distributed teams"
    }
]


def load_sample_data():
    """Load sample data into the database"""
    init_db()
    print("Database initialized.")

    with get_db() as db:
        # Check if data already exists
        existing_brands = db.query(Brand).count()
        if existing_brands > 0:
            print(f"Database already has {existing_brands} brands. Skipping sample data load.")
            print("To reload, delete the aeo_tracker.db file first.")
            return

        # Add brands
        brand_map = {}
        for brand_data in SAMPLE_BRANDS:
            brand = Brand(**brand_data)
            db.add(brand)
            db.flush()  # Get the ID
            brand_map[brand_data["name"]] = brand.id
            print(f"Added brand: {brand.name}")

        # Add questions for Your360 AI
        for q_data in YOUR360_QUESTIONS:
            question = Question(
                brand_id=brand_map["Your360 AI"],
                priority=5,
                is_active=True,
                **q_data
            )
            db.add(question)
        print(f"Added {len(YOUR360_QUESTIONS)} questions for Your360 AI")

        # Add questions for Webflow
        for q_data in WEBFLOW_QUESTIONS:
            question = Question(
                brand_id=brand_map["Webflow"],
                priority=5,
                is_active=True,
                **q_data
            )
            db.add(question)
        print(f"Added {len(WEBFLOW_QUESTIONS)} questions for Webflow")

        # Add content for Your360 AI
        for c_data in YOUR360_CONTENT:
            content = Content(
                brand_id=brand_map["Your360 AI"],
                published_at=datetime.now() - timedelta(days=7),
                is_published=True,
                **c_data
            )
            db.add(content)
        print(f"Added {len(YOUR360_CONTENT)} content items for Your360 AI")

        db.commit()
        print("\nSample data loaded successfully!")
        print("\nTo run the app: streamlit run app.py")


if __name__ == "__main__":
    load_sample_data()
