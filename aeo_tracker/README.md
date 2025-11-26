# AEO Tracker - Answer Engine Optimization

Track and optimize your brand's visibility across AI/LLM platforms like ChatGPT, Claude, and Gemini.

Based on **Ethan Smith's 4-Step AEO Methodology** (Graphite - works with Webflow, Rippling, Notion, etc.)

## What is AEO?

**Answer Engine Optimization (AEO)** is the practice of optimizing your brand's visibility in AI-generated responses. Unlike traditional SEO which focuses on search engine rankings, AEO focuses on getting your brand mentioned and recommended by Large Language Models.

### The Key Insight

> "Google SEO checks what sites LINK to you. LLMs check what sites SAY about you."

## Ethan's 4-Step Methodology

### Step 1: See What Customers Are Asking
Convert your paid search keywords into natural LLM questions.

**Example:**
- Paid keyword: "website builder for designers"
- Target LLM question: "What's the best website builder for a freelance designer who wants visual control and doesn't code?"

### Step 2: Check Your Current Visibility
Track your visibility across LLMs:
- Which prompts mention your brand
- Which sources LLMs cite
- Whether you appear at all

### Step 3: Publish Answers Where LLMs Look

**Offsite wins:**
- YouTube tutorials (LLMs love these!)
- Reddit answers
- Quora, StackOverflow
- LinkedIn posts

**On your site:**
- Use-case landing pages ("Website builder for restaurants")
- Template pages
- Help center articles
- Integration pages

### Step 4: Test Like a Scientist
Run controlled experiments:
1. Pick 50 target questions
2. Track visibility for 2 weeks (control period)
3. Add one type of content (e.g., YouTube tutorials)
4. Track for 4 weeks (test period)
5. Compare results

## Features

- **Brand Management**: Track multiple brands with keywords and competitors
- **Question Tracking**: Convert keywords to LLM questions, track visibility
- **Multi-LLM Support**: Query ChatGPT, Claude, and Gemini simultaneously
- **Visibility Analysis**: Detect if your brand is featured, mentioned, or listed
- **Content Registry**: Track published content across platforms
- **A/B Experiments**: Run scientific experiments on content changes
- **Historical Data**: Track visibility trends over time

## Installation

```bash
# Navigate to the aeo_tracker directory
cd aeo_tracker

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file with your API keys:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
```

## Usage

```bash
# Run the Streamlit app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

### Quick Start

1. **Add a Brand**: Go to Brands > Add Brand
   - Enter your brand name, domain, keywords, and competitors

2. **Add Questions**: Go to Questions > Generate from Keyword
   - Enter a keyword like "project management software"
   - Select generated questions to track

3. **Run Visibility Check**: Go to Visibility Check
   - Select your brand and a question
   - Choose LLMs to query
   - Click "Run Visibility Check"

4. **Create an Experiment**: Go to Experiments > Create Experiment
   - Define your hypothesis
   - Select target questions
   - Start the control period
   - After publishing new content, start the test period
   - Analyze results

## Project Structure

```
aeo_tracker/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration settings
├── requirements.txt       # Dependencies
├── database/
│   ├── models.py          # SQLAlchemy models
│   └── db.py              # Database connection
├── services/
│   ├── llm_service.py     # Multi-LLM querying
│   ├── visibility.py      # Visibility analysis
│   └── experiments.py     # Experiment management
└── utils/
    └── helpers.py         # Utility functions
```

## Database Models

- **Brand**: Company/product being tracked
- **Question**: Target LLM questions to rank for
- **Content**: Published content across platforms
- **VisibilityCheck**: Individual visibility check results
- **Experiment**: A/B experiments with control/test periods

## Visibility Scoring

| Status | Score | Description |
|--------|-------|-------------|
| Featured | 100 | Brand prominently recommended |
| Mentioned | 70 | Brand mentioned positively |
| Listed | 40 | Brand appears in a list |
| Cited Source | 30 | Brand's content cited |
| Not Found | 0 | Brand doesn't appear |

## Example Workflow

### For a new tool like "Your360 AI" (anonymous feedback tool):

1. **Add Brand**: Your360 AI with keywords ["Your360", "your360.ai"]
2. **Add Questions**:
   - "What's the best tool for anonymous team feedback?"
   - "How can I get honest feedback from my team?"
   - "Best 360 review tools for small teams?"
3. **Check Initial Visibility**: Probably low/not found
4. **Create Experiment**: "YouTube Tutorial Impact Test"
5. **Start Control Period**: 2 weeks of visibility tracking
6. **Publish Content**:
   - 5 YouTube videos ("How to give hard feedback", etc.)
   - Reddit answers on r/management
   - Integration pages (Slack, Teams)
   - Submit to Product Hunt
7. **Start Test Period**: 4 weeks of tracking
8. **Analyze Results**: Compare control vs test visibility

## Supported LLMs

- **ChatGPT** (GPT-4o) via OpenAI API
- **Claude** (Sonnet) via Anthropic API
- **Gemini** (1.5 Flash) via Google AI API

## Tips for Better AEO

1. **YouTube is powerful**: LLMs heavily cite YouTube content
2. **Reddit matters**: Authentic community discussions influence LLMs
3. **Help docs rank**: Detailed help center articles get cited
4. **Integration pages work**: "Works with X" pages improve visibility
5. **Be specific**: Target long-tail questions, not just broad topics
6. **Test systematically**: One content type at a time, measure impact

## Credits

Based on the AEO methodology shared by **Ethan Smith** of [Graphite](https://graphite.dev), who works with companies like Webflow, Rippling, and Notion to optimize their LLM visibility.

## License

MIT License
