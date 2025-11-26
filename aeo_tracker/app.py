"""
AEO Tracker - Answer Engine Optimization Tracking Application

A Streamlit application for tracking brand visibility across AI/LLM platforms.
Based on Ethan Smith's 4-step AEO methodology.

Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# Initialize database on import
from database.db import init_db, get_db
from database.models import Brand, Question, Content, VisibilityCheck, Experiment
from services.llm_service import LLMService
from services.visibility import VisibilityAnalyzer
from services.experiments import ExperimentManager
from utils.helpers import (
    keyword_to_question,
    generate_question_variations,
    format_visibility_score,
    format_visibility_status
)
from config import CONTENT_TYPES, LLM_MODELS, VISIBILITY_SCORES

# Initialize database
init_db()

# Page config
st.set_page_config(
    page_title="AEO Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .status-featured { color: #28a745; font-weight: bold; }
    .status-mentioned { color: #007bff; }
    .status-listed { color: #ffc107; }
    .status-not_found { color: #dc3545; }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point"""
    st.title("📊 AEO Tracker")
    st.markdown("*Answer Engine Optimization - Track your brand visibility across AI platforms*")

    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            [
                "🏠 Dashboard",
                "🏢 Brands",
                "❓ Questions",
                "📝 Content",
                "🔍 Visibility Check",
                "🧪 Experiments",
                "⚙️ Settings"
            ]
        )

    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🏢 Brands":
        show_brands_page()
    elif page == "❓ Questions":
        show_questions_page()
    elif page == "📝 Content":
        show_content_page()
    elif page == "🔍 Visibility Check":
        show_visibility_check_page()
    elif page == "🧪 Experiments":
        show_experiments_page()
    elif page == "⚙️ Settings":
        show_settings_page()


def show_dashboard():
    """Dashboard overview page"""
    st.header("Dashboard")

    with get_db() as db:
        # Summary metrics
        brands_count = db.query(Brand).count()
        questions_count = db.query(Question).count()
        checks_count = db.query(VisibilityCheck).count()
        experiments_count = db.query(Experiment).count()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Brands", brands_count)
        with col2:
            st.metric("Questions Tracked", questions_count)
        with col3:
            st.metric("Visibility Checks", checks_count)
        with col4:
            st.metric("Experiments", experiments_count)

        st.divider()

        # Recent visibility checks
        st.subheader("Recent Visibility Checks")

        recent_checks = db.query(VisibilityCheck).order_by(
            VisibilityCheck.checked_at.desc()
        ).limit(10).all()

        if recent_checks:
            check_data = []
            for check in recent_checks:
                question = db.query(Question).filter(Question.id == check.question_id).first()
                check_data.append({
                    "Date": check.checked_at.strftime("%Y-%m-%d %H:%M"),
                    "LLM": check.llm_provider,
                    "Question": question.question_text[:50] + "..." if question else "N/A",
                    "Status": check.visibility_status,
                    "Score": check.visibility_score or 0
                })

            df = pd.DataFrame(check_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No visibility checks yet. Go to 'Visibility Check' to run your first check!")

        # Active experiments
        st.subheader("Active Experiments")

        active_experiments = db.query(Experiment).filter(
            Experiment.status.in_(["control_period", "test_period"])
        ).all()

        if active_experiments:
            for exp in active_experiments:
                with st.expander(f"📊 {exp.name} - {exp.status}"):
                    st.write(f"**Hypothesis:** {exp.hypothesis}")
                    if exp.status == "control_period" and exp.control_end:
                        days_left = (exp.control_end - datetime.utcnow()).days
                        st.write(f"Control period ends in {days_left} days")
                    elif exp.status == "test_period" and exp.test_end:
                        days_left = (exp.test_end - datetime.utcnow()).days
                        st.write(f"Test period ends in {days_left} days")
        else:
            st.info("No active experiments. Go to 'Experiments' to start one!")

    # Methodology reminder
    st.divider()
    with st.expander("📚 Ethan Smith's 4-Step AEO Methodology"):
        st.markdown("""
        **Step 1: See what customers are asking**
        - Convert paid search keywords to natural LLM questions

        **Step 2: Check your current visibility on LLMs**
        - Track which prompts mention your brand
        - See which sources LLMs cite

        **Step 3: Publish answers where LLMs look**
        - YouTube tutorials, Reddit answers, Landing pages
        - Help center articles, Integration pages

        **Step 4: Test like a scientist**
        - Run controlled experiments
        - Compare visibility before/after content changes
        """)


def show_brands_page():
    """Brand management page"""
    st.header("🏢 Brand Management")

    tab1, tab2 = st.tabs(["View Brands", "Add Brand"])

    with tab1:
        with get_db() as db:
            brands = db.query(Brand).all()

            if brands:
                for brand in brands:
                    with st.expander(f"**{brand.name}**", expanded=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Domain:** {brand.domain or 'Not set'}")
                            st.write(f"**Description:** {brand.description or 'Not set'}")

                        with col2:
                            keywords = brand.keywords or []
                            competitors = brand.competitors or []
                            st.write(f"**Keywords:** {', '.join(keywords) if keywords else 'None'}")
                            st.write(f"**Competitors:** {', '.join(competitors) if competitors else 'None'}")

                        # Delete button
                        if st.button(f"Delete {brand.name}", key=f"del_brand_{brand.id}"):
                            db.delete(brand)
                            db.commit()
                            st.rerun()
            else:
                st.info("No brands added yet. Add your first brand to get started!")

    with tab2:
        st.subheader("Add New Brand")

        with st.form("add_brand_form"):
            name = st.text_input("Brand Name*", placeholder="e.g., Webflow")
            domain = st.text_input("Domain", placeholder="e.g., webflow.com")
            description = st.text_area("Description", placeholder="What does your brand/product do?")

            keywords_input = st.text_input(
                "Keywords (comma-separated)",
                placeholder="e.g., Webflow, webflow.com, Webflow Inc"
            )

            competitors_input = st.text_input(
                "Competitors (comma-separated)",
                placeholder="e.g., Wix, Squarespace, WordPress"
            )

            submitted = st.form_submit_button("Add Brand")

            if submitted and name:
                keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
                competitors = [c.strip() for c in competitors_input.split(",") if c.strip()]

                with get_db() as db:
                    brand = Brand(
                        name=name,
                        domain=domain,
                        description=description,
                        keywords=keywords,
                        competitors=competitors
                    )
                    db.add(brand)
                    db.commit()

                st.success(f"Brand '{name}' added successfully!")
                st.rerun()


def show_questions_page():
    """Question management page"""
    st.header("❓ Question Management")

    tab1, tab2, tab3 = st.tabs(["View Questions", "Add Question", "Generate from Keyword"])

    with get_db() as db:
        brands = db.query(Brand).all()

    if not brands:
        st.warning("Please add a brand first before creating questions.")
        return

    brand_options = {b.name: b.id for b in brands}

    with tab1:
        st.subheader("Tracked Questions")

        # Filter by brand
        selected_brand = st.selectbox("Filter by Brand", ["All"] + list(brand_options.keys()))

        with get_db() as db:
            if selected_brand == "All":
                questions = db.query(Question).all()
            else:
                brand_id = brand_options[selected_brand]
                questions = db.query(Question).filter(Question.brand_id == brand_id).all()

            if questions:
                for q in questions:
                    brand = db.query(Brand).filter(Brand.id == q.brand_id).first()
                    with st.expander(f"**{q.question_text[:80]}...**" if len(q.question_text) > 80 else f"**{q.question_text}**"):
                        st.write(f"**Brand:** {brand.name if brand else 'Unknown'}")
                        st.write(f"**Source Keyword:** {q.source_keyword or 'N/A'}")
                        st.write(f"**Category:** {q.category or 'N/A'}")
                        st.write(f"**Priority:** {q.priority}/10")
                        st.write(f"**Active:** {'Yes' if q.is_active else 'No'}")

                        if st.button(f"Delete", key=f"del_q_{q.id}"):
                            db.delete(q)
                            db.commit()
                            st.rerun()
            else:
                st.info("No questions found. Add questions to start tracking visibility!")

    with tab2:
        st.subheader("Add Question Manually")

        with st.form("add_question_form"):
            brand_name = st.selectbox("Brand*", list(brand_options.keys()))
            question_text = st.text_area(
                "Question*",
                placeholder="What's the best website builder for freelance designers?"
            )
            source_keyword = st.text_input("Source Keyword", placeholder="website builder for designers")
            category = st.selectbox("Category", ["", "product comparison", "how-to", "best for", "review", "alternative", "pricing", "features"])
            priority = st.slider("Priority", 1, 10, 5)

            submitted = st.form_submit_button("Add Question")

            if submitted and question_text:
                with get_db() as db:
                    question = Question(
                        brand_id=brand_options[brand_name],
                        question_text=question_text,
                        source_keyword=source_keyword,
                        category=category if category else None,
                        priority=priority,
                        is_active=True
                    )
                    db.add(question)
                    db.commit()

                st.success("Question added successfully!")
                st.rerun()

    with tab3:
        st.subheader("Generate Questions from Keywords")
        st.markdown("*Convert paid search keywords to natural LLM questions*")

        with st.form("generate_questions_form"):
            brand_name = st.selectbox("Brand*", list(brand_options.keys()), key="gen_brand")
            keyword = st.text_input("Keyword*", placeholder="e.g., website builder for designers")
            num_variations = st.slider("Number of variations", 1, 10, 5)

            generate = st.form_submit_button("Generate Questions")

        if generate and keyword:
            questions = generate_question_variations(keyword, num_variations)

            st.subheader("Generated Questions")
            selected_questions = []

            for i, q in enumerate(questions):
                if st.checkbox(q, value=True, key=f"gen_q_{i}"):
                    selected_questions.append(q)

            if st.button("Add Selected Questions"):
                with get_db() as db:
                    for q_text in selected_questions:
                        question = Question(
                            brand_id=brand_options[brand_name],
                            question_text=q_text,
                            source_keyword=keyword,
                            is_active=True
                        )
                        db.add(question)
                    db.commit()

                st.success(f"Added {len(selected_questions)} questions!")
                st.rerun()


def show_content_page():
    """Content tracking page"""
    st.header("📝 Content Registry")
    st.markdown("*Track published content that helps LLMs find you*")

    tab1, tab2 = st.tabs(["View Content", "Add Content"])

    with get_db() as db:
        brands = db.query(Brand).all()

    if not brands:
        st.warning("Please add a brand first.")
        return

    brand_options = {b.name: b.id for b in brands}

    with tab1:
        with get_db() as db:
            contents = db.query(Content).order_by(Content.created_at.desc()).all()

            if contents:
                # Group by type
                st.markdown("### Content by Type")

                content_by_type = {}
                for c in contents:
                    if c.content_type not in content_by_type:
                        content_by_type[c.content_type] = []
                    content_by_type[c.content_type].append(c)

                for content_type, items in content_by_type.items():
                    with st.expander(f"**{content_type}** ({len(items)} items)"):
                        for item in items:
                            st.markdown(f"- [{item.title}]({item.url})" if item.url else f"- {item.title}")
            else:
                st.info("No content tracked yet. Add content you've published to track its impact!")

    with tab2:
        st.subheader("Add Content")

        with st.form("add_content_form"):
            brand_name = st.selectbox("Brand*", list(brand_options.keys()))
            title = st.text_input("Title*", placeholder="How to Build a Portfolio Website")
            content_type = st.selectbox("Content Type*", CONTENT_TYPES)
            url = st.text_input("URL", placeholder="https://youtube.com/watch?v=...")
            description = st.text_area("Description", placeholder="Brief description of the content")

            col1, col2 = st.columns(2)
            with col1:
                platform = st.text_input("Platform", placeholder="youtube.com")
            with col2:
                published_at = st.date_input("Published Date", value=datetime.now())

            keywords = st.text_input("Target Keywords (comma-separated)")

            submitted = st.form_submit_button("Add Content")

            if submitted and title and content_type:
                target_keywords = [k.strip() for k in keywords.split(",") if k.strip()]

                with get_db() as db:
                    content = Content(
                        brand_id=brand_options[brand_name],
                        title=title,
                        content_type=content_type,
                        url=url,
                        platform=platform,
                        description=description,
                        target_keywords=target_keywords,
                        published_at=datetime.combine(published_at, datetime.min.time()),
                        is_published=True
                    )
                    db.add(content)
                    db.commit()

                st.success("Content added successfully!")
                st.rerun()


def show_visibility_check_page():
    """Run visibility checks"""
    st.header("🔍 Visibility Check")
    st.markdown("*Check how your brand appears in LLM responses*")

    # Initialize services
    llm_service = LLMService()
    analyzer = VisibilityAnalyzer(llm_service)

    # Show available providers
    available = llm_service.get_available_providers()

    if not available:
        st.error("No LLM providers configured. Please add API keys in Settings.")
        return

    st.success(f"Available LLMs: {', '.join([p['display_name'] for p in available])}")

    with get_db() as db:
        brands = db.query(Brand).all()

    if not brands:
        st.warning("Please add a brand first.")
        return

    brand_options = {b.name: b.id for b in brands}

    tab1, tab2 = st.tabs(["Quick Check", "Batch Check"])

    with tab1:
        st.subheader("Quick Visibility Check")

        brand_name = st.selectbox("Select Brand", list(brand_options.keys()))

        with get_db() as db:
            brand = db.query(Brand).filter(Brand.id == brand_options[brand_name]).first()
            questions = db.query(Question).filter(
                Question.brand_id == brand.id,
                Question.is_active == True
            ).all()

        if not questions:
            st.warning("No active questions for this brand. Add questions first.")
            return

        question_options = {q.question_text[:80]: q.id for q in questions}
        selected_question = st.selectbox("Select Question", list(question_options.keys()))

        llm_options = [p["key"] for p in available]
        selected_llms = st.multiselect(
            "Select LLMs to check",
            llm_options,
            default=llm_options
        )

        if st.button("Run Visibility Check", type="primary"):
            with st.spinner("Checking visibility across LLMs..."):
                question = db.query(Question).filter(
                    Question.id == question_options[selected_question]
                ).first()

                results = []
                for llm_key in selected_llms:
                    response = llm_service.query(llm_key, question.question_text)

                    if response.success:
                        result = analyzer.analyze_response(
                            response_text=response.response_text,
                            brand_name=brand.name,
                            brand_keywords=brand.keywords or [],
                            competitors=brand.competitors or [],
                            llm_provider=response.provider,
                            llm_model=response.model,
                            question=question.question_text
                        )
                        results.append(result)

                        # Save to database
                        analyzer.save_visibility_check(result, question.id)
                    else:
                        st.error(f"{llm_key}: {response.error}")

                # Display results
                st.subheader("Results")

                for result in results:
                    status_info = format_visibility_status(result.visibility_status)

                    with st.expander(f"**{result.llm_provider}** - {status_info['label']} ({result.visibility_score}/100)"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric("Visibility Score", f"{result.visibility_score}/100")
                            st.write(f"**Status:** {result.visibility_status}")
                            if result.position_in_list:
                                st.write(f"**Position:** #{result.position_in_list}")

                        with col2:
                            if result.competitors_found:
                                st.write(f"**Competitors Found:** {', '.join(result.competitors_found)}")
                            if result.cited_sources:
                                st.write(f"**Sources Cited:** {len(result.cited_sources)}")

                        st.markdown("**Response:**")
                        st.text_area("", result.response_text, height=200, key=f"resp_{result.llm_provider}")

                        if result.mention_context:
                            st.markdown("**Context:**")
                            st.info(result.mention_context)

    with tab2:
        st.subheader("Batch Visibility Check")
        st.markdown("Check all active questions for a brand across all LLMs")

        brand_name = st.selectbox("Select Brand for Batch", list(brand_options.keys()), key="batch_brand")

        with get_db() as db:
            brand = db.query(Brand).filter(Brand.id == brand_options[brand_name]).first()
            questions = db.query(Question).filter(
                Question.brand_id == brand.id,
                Question.is_active == True
            ).all()

        st.info(f"This will check {len(questions)} questions across {len(available)} LLMs ({len(questions) * len(available)} total checks)")

        if st.button("Run Batch Check", type="primary"):
            progress = st.progress(0)
            status = st.empty()

            total = len(questions) * len(available)
            current = 0

            all_results = []

            for question in questions:
                for llm_info in available:
                    current += 1
                    progress.progress(current / total)
                    status.text(f"Checking {llm_info['display_name']} - {question.question_text[:40]}...")

                    response = llm_service.query(llm_info["key"], question.question_text)

                    if response.success:
                        result = analyzer.analyze_response(
                            response_text=response.response_text,
                            brand_name=brand.name,
                            brand_keywords=brand.keywords or [],
                            competitors=brand.competitors or [],
                            llm_provider=response.provider,
                            llm_model=response.model,
                            question=question.question_text
                        )
                        analyzer.save_visibility_check(result, question.id)
                        all_results.append({
                            "Question": question.question_text[:50],
                            "LLM": llm_info["display_name"],
                            "Status": result.visibility_status,
                            "Score": result.visibility_score
                        })

            status.text("Complete!")

            # Summary
            if all_results:
                df = pd.DataFrame(all_results)
                st.dataframe(df, use_container_width=True)

                # Aggregate metrics
                avg_score = df["Score"].mean()
                st.metric("Average Visibility Score", f"{avg_score:.1f}/100")


def show_experiments_page():
    """Experiment management page"""
    st.header("🧪 Experiments")
    st.markdown("*Test content changes like a scientist*")

    tab1, tab2, tab3 = st.tabs(["Active Experiments", "Create Experiment", "Results"])

    exp_manager = ExperimentManager()

    with get_db() as db:
        brands = db.query(Brand).all()

    if not brands:
        st.warning("Please add a brand first.")
        return

    brand_options = {b.name: b.id for b in brands}

    with tab1:
        st.subheader("Active Experiments")

        with get_db() as db:
            experiments = db.query(Experiment).filter(
                Experiment.status.in_(["draft", "control_period", "test_period"])
            ).all()

            if experiments:
                for exp in experiments:
                    brand = db.query(Brand).filter(Brand.id == exp.brand_id).first()

                    with st.expander(f"**{exp.name}** - {exp.status}"):
                        st.write(f"**Brand:** {brand.name if brand else 'Unknown'}")
                        st.write(f"**Hypothesis:** {exp.hypothesis}")
                        st.write(f"**Status:** {exp.status}")

                        if exp.status == "draft":
                            if st.button("Start Control Period", key=f"start_{exp.id}"):
                                exp_manager.start_control_period(exp.id)
                                st.success("Control period started!")
                                st.rerun()

                        elif exp.status == "control_period":
                            st.write(f"**Control Period:** {exp.control_start} to {exp.control_end}")

                            content_desc = st.text_area(
                                "Content Intervention Description",
                                placeholder="Describe what content you're adding (e.g., '5 YouTube tutorials on feedback techniques')",
                                key=f"content_{exp.id}"
                            )

                            if st.button("Start Test Period", key=f"test_{exp.id}"):
                                exp_manager.start_test_period(exp.id, content_desc)
                                st.success("Test period started!")
                                st.rerun()

                        elif exp.status == "test_period":
                            st.write(f"**Test Period:** {exp.test_start} to {exp.test_end}")
                            st.write(f"**Intervention:** {exp.content_intervention}")

                            if st.button("Complete Experiment", key=f"complete_{exp.id}"):
                                exp_manager.complete_experiment(exp.id)
                                st.success("Experiment completed! View results in the Results tab.")
                                st.rerun()

                        # Run visibility checks
                        if exp.status in ["control_period", "test_period"]:
                            if st.button("Run Visibility Checks", key=f"check_{exp.id}"):
                                with st.spinner("Running checks..."):
                                    checks = exp_manager.run_visibility_checks(exp.id)
                                    st.success(f"Completed {len(checks)} visibility checks!")
            else:
                st.info("No active experiments. Create one to start testing!")

    with tab2:
        st.subheader("Create New Experiment")

        with st.form("create_experiment_form"):
            name = st.text_input("Experiment Name*", placeholder="YouTube Tutorial Impact Test")
            brand_name = st.selectbox("Brand*", list(brand_options.keys()))

            with get_db() as db:
                brand_id = brand_options[brand_name]
                questions = db.query(Question).filter(
                    Question.brand_id == brand_id,
                    Question.is_active == True
                ).all()

            question_options = {q.question_text[:60]: q.id for q in questions}

            if questions:
                selected_questions = st.multiselect(
                    "Target Questions*",
                    list(question_options.keys())
                )
            else:
                st.warning("No active questions for this brand")
                selected_questions = []

            hypothesis = st.text_area(
                "Hypothesis*",
                placeholder="Adding YouTube tutorials will increase brand visibility by 20%"
            )

            description = st.text_area(
                "Description",
                placeholder="Detailed experiment description..."
            )

            submitted = st.form_submit_button("Create Experiment")

            if submitted and name and hypothesis and selected_questions:
                target_ids = [question_options[q] for q in selected_questions]

                experiment = exp_manager.create_experiment(
                    brand_id=brand_options[brand_name],
                    name=name,
                    hypothesis=hypothesis,
                    target_question_ids=target_ids,
                    description=description
                )

                st.success(f"Experiment '{name}' created! Start the control period when ready.")
                st.rerun()

    with tab3:
        st.subheader("Experiment Results")

        with get_db() as db:
            completed = db.query(Experiment).filter(
                Experiment.status == "completed"
            ).all()

            if completed:
                for exp in completed:
                    brand = db.query(Brand).filter(Brand.id == exp.brand_id).first()

                    with st.expander(f"**{exp.name}** - {brand.name if brand else 'Unknown'}"):
                        results = exp_manager.analyze_experiment(exp.id)

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Control Avg Score",
                                f"{results.control_avg_score:.1f}",
                                help=f"Based on {results.control_checks} checks"
                            )

                        with col2:
                            st.metric(
                                "Test Avg Score",
                                f"{results.test_avg_score:.1f}",
                                delta=f"{results.score_change:+.1f}%",
                                help=f"Based on {results.test_checks} checks"
                            )

                        with col3:
                            sig_text = "Yes" if results.is_significant else "No"
                            st.metric("Statistically Significant", sig_text)

                        st.write(f"**Hypothesis:** {exp.hypothesis}")
                        st.write(f"**Intervention:** {exp.content_intervention}")
                        st.write(f"**Confidence:** {results.confidence_level}")

                        if results.by_provider:
                            st.markdown("**By Provider:**")
                            provider_df = pd.DataFrame([
                                {
                                    "Provider": p,
                                    "Control": d["control_avg"],
                                    "Test": d["test_avg"],
                                    "Change": d["change"]
                                }
                                for p, d in results.by_provider.items()
                            ])
                            st.dataframe(provider_df, use_container_width=True)
            else:
                st.info("No completed experiments yet.")


def show_settings_page():
    """Settings and configuration page"""
    st.header("⚙️ Settings")

    st.subheader("LLM API Configuration")

    llm_service = LLMService()
    available = llm_service.get_available_providers()

    # Show status of each provider
    for llm_key, config in LLM_MODELS.items():
        provider = config["provider"]
        is_available = any(p["key"] == llm_key for p in available)

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**{config['display_name']}**")

        with col2:
            st.write(f"Model: `{config['model']}`")

        with col3:
            if is_available:
                st.success("Configured")
            else:
                st.error("Not configured")

    st.divider()

    st.markdown("""
    ### API Key Setup

    Add your API keys to a `.env` file in the `aeo_tracker` directory:

    ```
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
    GOOGLE_API_KEY=AI...
    ```

    Or set them as environment variables.
    """)

    st.divider()

    st.subheader("Visibility Scoring")

    st.markdown("Current scoring weights:")

    for status, score in VISIBILITY_SCORES.items():
        st.write(f"- **{status}:** {score} points")

    st.divider()

    st.subheader("Database")

    with get_db() as db:
        brands_count = db.query(Brand).count()
        questions_count = db.query(Question).count()
        checks_count = db.query(VisibilityCheck).count()

    st.write(f"- Brands: {brands_count}")
    st.write(f"- Questions: {questions_count}")
    st.write(f"- Visibility Checks: {checks_count}")

    if st.button("Export Database (Coming Soon)", disabled=True):
        pass


if __name__ == "__main__":
    main()
