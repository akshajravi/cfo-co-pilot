"""
CFO Copilot - Streamlit Application

A professional financial analysis assistant that provides insights into 
financial performance through natural language queries.

Author: CFO Copilot Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any
import streamlit as st
from agent.planner import CFOAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application configuration constants
APP_CONFIG = {
    "page_title": "CFO Copilot",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Page configuration
st.set_page_config(
    page_title=APP_CONFIG["page_title"],
    page_icon=APP_CONFIG["page_icon"],
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["initial_sidebar_state"]
)

def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if 'agent' not in st.session_state:
        try:
            st.session_state.agent = CFOAgent()
            logger.info("CFO Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CFO Agent: {e}")
            st.error("Failed to initialize the financial analysis agent. Please refresh the page.")
            return

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def render_header() -> None:
    """Render the main application header."""
    st.title("📊 CFO Copilot")
    st.markdown(
        """
        <div style='margin-bottom: 2rem;'>
            <p style='font-size: 1.2rem; color: #666; margin: 0;'>
                Your intelligent financial analysis assistant
            </p>
            <p style='color: #888; margin: 0.5rem 0 0 0;'>
                Ask questions about financial performance and get instant insights
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

def get_sample_questions() -> List[str]:
    """Get predefined sample questions for user guidance."""
    return [
        "What was June 2025 revenue vs budget in USD?",
        "Show Gross Margin % trend for the last 3 months",
        "Break down Opex by category for June",
        "What is our cash runway right now?"
    ]

def render_sidebar() -> None:
    """Render the sidebar with sample questions and data status."""
    st.sidebar.markdown("### 💡 Sample Questions")
    st.sidebar.markdown("*Click any question to try it out*")
    
    sample_questions = get_sample_questions()
    
    # Create a text input placeholder
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""

    # Sample question buttons
    for i, question in enumerate(sample_questions):
        if st.sidebar.button(question, key=f"sample_{i}", use_container_width=True):
            st.session_state.current_question = question

# Initialize session state
initialize_session_state()

# Render header
render_header()

# Render sidebar
render_sidebar()

def render_chat_interface() -> None:
    """Render the main chat interface for user input."""
    st.markdown("### 💬 Ask a Question")
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            question = st.text_input(
                "Enter your financial question:",
                value=st.session_state.current_question,
                key="question_input",
                placeholder="e.g., What was our revenue last month compared to budget?"
            )
        
        with col2:
            submit_button = st.button("Ask", type="primary", use_container_width=True)
    
    return question, submit_button

def process_question(question: str) -> None:
    """Process a user question and update chat history."""
    try:
        with st.spinner("🔍 Analyzing financial data..."):
            response = st.session_state.agent.process_question(question)
            st.session_state.chat_history.append({
                'question': question,
                'response': response
            })
            logger.info(f"Successfully processed question: {question[:50]}...")
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        st.error("Sorry, I encountered an error while processing your question. Please try again.")
    finally:
        # Clear the current question after processing
        st.session_state.current_question = ""
        st.rerun()

# Render chat interface
question, submit_button = render_chat_interface()

# Process question if submitted
if submit_button and question.strip():
    process_question(question)

def render_chat_history() -> None:
    """Render the chat history with questions and responses."""
    if not st.session_state.chat_history:
        return
    
    st.markdown("### 📊 Analysis Results")
    
    # Show newest first
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(f"Q: {chat['question']}", expanded=(i == 0)):
            # Show response text
            st.markdown(f"**Analysis:** {chat['response']['text']}")
            
            # Show chart if exists
            if chat['response'].get('chart') is not None:
                st.plotly_chart(chat['response']['chart'], use_container_width=True)
            
            # Optional raw data display
            if chat['response'].get('data') is not None:
                with st.expander("📋 View Raw Data", expanded=False):
                    st.json(chat['response']['data'])

def render_dashboard_overview() -> None:
    """Render the financial dashboard overview when no chat history exists."""
    st.markdown("### 📈 Financial Dashboard")
    st.markdown("*Start by asking a question or try one of the sample questions from the sidebar*")
    
    # Display sample metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Current Month Revenue",
            value="$125K",
            delta="5%",
            help="Revenue for the current month compared to previous month"
        )
    
    with col2:
        st.metric(
            label="Gross Margin",
            value="65.2%",
            delta="2.1%",
            help="Gross margin percentage with month-over-month change"
        )
    
    with col3:
        st.metric(
            label="Cash Runway",
            value="8.5 months",
            delta="-0.5 months",
            help="Estimated months of cash remaining at current burn rate"
        )

# Display content based on chat history
if st.session_state.chat_history:
    render_chat_history()
else:
    render_dashboard_overview()

def render_sidebar_footer() -> None:
    """Render the sidebar footer with data status and record counts."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Data Status")
    
    try:
        # Validate agent exists
        if 'agent' not in st.session_state or not hasattr(st.session_state.agent, 'tools'):
            st.sidebar.markdown("⚠️ Agent not properly initialized")
            return
            
        # Get data counts safely
        tools = st.session_state.agent.tools
        data_info = {
            "Actuals": getattr(tools, 'actuals_df', None),
            "Budget": getattr(tools, 'budget_df', None),
            "Cash": getattr(tools, 'cash_df', None),
            "FX Rates": getattr(tools, 'fx_df', None)
        }
        
        # Check if data is loaded
        loaded_datasets = []
        record_counts = {}
        
        for name, df in data_info.items():
            if df is not None and hasattr(df, '__len__'):
                count = len(df)
                record_counts[name] = count
                if count > 0:
                    loaded_datasets.append(name)
        
        if loaded_datasets:
            st.sidebar.markdown("✅ Financial data loaded")
            
            # Show record counts
            counts_text = "**Record Counts:**\n"
            for name, count in record_counts.items():
                status = "✅" if count > 0 else "⚠️"
                counts_text += f"- {name}: {status} {count:,}\n"
            
            st.sidebar.markdown(counts_text)
        else:
            st.sidebar.markdown("⚠️ No financial data loaded")
            
    except Exception as e:
        logger.error(f"Error displaying data status: {e}")
        st.sidebar.markdown("⚠️ Error loading data status")

# Render sidebar footer
render_sidebar_footer()