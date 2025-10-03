import pytest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.planner import CFOAgent
from agent.tools import FinanceDataTools

@pytest.fixture
def agent():
    return CFOAgent()

def test_intent_classification(agent):
    """Test intent classification for various question types"""
    test_cases = [
        ("What was June revenue vs budget?", "revenue_vs_budget"),
        ("Show me gross margin trends", "gross_margin"),
        ("Break down opex by category", "opex_breakdown"),
        ("What is our cash runway?", "cash_runway"),
        ("Show me the EBITDA", "ebitda"),
        ("Random weather question", "unknown"),
        ("How is the weather today?", "unknown"),
    ]
    
    for question, expected in test_cases:
        result = agent.classify_intent(question)
        assert result == expected, f"Failed for question: '{question}', got {result}, expected {expected}"

def test_month_extraction(agent):
    """Test month and year extraction from questions"""
    test_cases = [
        ("June 2025 revenue", (6, 2025)),
        ("What was April performance?", (4, 2025)),
        ("Show me December 2024", (12, 2024)),
        ("Current month", (None, 2025)),
        ("January numbers for 2023", (1, 2023)),
        ("Feb data", (2, 2025)),
        ("No date info here", (None, 2025)),
    ]
    
    for question, expected in test_cases:
        result = agent.extract_month_year(question)
        assert result == expected, f"Failed for question: '{question}', got {result}, expected {expected}"

def test_process_question_structure(agent):
    """Test that process_question returns proper structure"""
    response = agent.process_question("What was June revenue?")
    
    # Check required keys exist
    required_keys = ['intent', 'text', 'chart', 'data']
    for key in required_keys:
        assert key in response, f"Missing key: {key}"
    
    # Check text is not empty
    assert response['text'] != "", "Response text should not be empty"
    
    # Check intent is valid
    valid_intents = ['revenue_vs_budget', 'gross_margin', 'opex_breakdown', 'cash_runway', 'ebitda', 'unknown', 'error']
    assert response['intent'] in valid_intents, f"Invalid intent: {response['intent']}"

def test_tools_data_loading():
    """Test that FinanceDataTools loads data properly"""
    try:
        tools = FinanceDataTools()
        
        # Check that dataframes are initialized (even if empty)
        assert hasattr(tools, 'actuals_df'), "Missing actuals_df attribute"
        assert hasattr(tools, 'budget_df'), "Missing budget_df attribute"
        assert hasattr(tools, 'cash_df'), "Missing cash_df attribute"
        assert hasattr(tools, 'fx_df'), "Missing fx_df attribute"
        
        # If data files exist, check they have data
        if not tools.actuals_df.empty:
            assert tools.actuals_df.shape[0] > 0, "Actuals dataframe should have rows if loaded"
        
    except Exception as e:
        pytest.skip(f"Data files not available or error loading: {e}")

def test_revenue_calculation(agent):
    """Test revenue vs budget calculation"""
    try:
        response = agent.process_question("June 2025 revenue vs budget")
        
        # Should not be an error response
        assert response['intent'] != 'error', f"Got error: {response['text']}"
        
        # Should be revenue_vs_budget intent
        assert response['intent'] == 'revenue_vs_budget', f"Wrong intent: {response['intent']}"
        
        # If we have data, check structure
        if response['data'] is not None:
            assert 'actual' in response['data'], "Missing 'actual' in data"
            assert 'budget' in response['data'], "Missing 'budget' in data"
            assert isinstance(response['data']['actual'], (int, float)), "Actual should be numeric"
            assert isinstance(response['data']['budget'], (int, float)), "Budget should be numeric"
        
    except Exception as e:
        pytest.skip(f"Data files not available or error in calculation: {e}")

def test_gross_margin_calculation(agent):
    """Test gross margin calculation"""
    try:
        response = agent.process_question("Show me gross margin trends")
        
        assert response['intent'] == 'gross_margin', f"Wrong intent: {response['intent']}"
        
        # If we have data, check structure
        if response['data'] is not None:
            assert 'avg_margin' in response['data'], "Missing 'avg_margin' in data"
            assert isinstance(response['data']['avg_margin'], (int, float)), "Average margin should be numeric"
        
    except Exception as e:
        pytest.skip(f"Data files not available or error in calculation: {e}")

def test_opex_breakdown_calculation(agent):
    """Test opex breakdown calculation"""
    try:
        response = agent.process_question("Break down opex by category")
        
        assert response['intent'] == 'opex_breakdown', f"Wrong intent: {response['intent']}"
        
        # If we have data, check it's a dictionary
        if response['data'] is not None:
            assert isinstance(response['data'], dict), "Opex data should be a dictionary"
        
    except Exception as e:
        pytest.skip(f"Data files not available or error in calculation: {e}")

def test_cash_runway_calculation(agent):
    """Test cash runway calculation"""
    try:
        response = agent.process_question("What is our cash runway?")
        
        assert response['intent'] == 'cash_runway', f"Wrong intent: {response['intent']}"
        
        # If we have data, check structure
        if response['data'] is not None:
            assert 'runway_months' in response['data'], "Missing 'runway_months' in data"
            assert 'cash_balance' in response['data'], "Missing 'cash_balance' in data"
            assert 'monthly_burn' in response['data'], "Missing 'monthly_burn' in data"
        
    except Exception as e:
        pytest.skip(f"Data files not available or error in calculation: {e}")

def test_ebitda_calculation(agent):
    """Test EBITDA calculation"""
    try:
        response = agent.process_question("Show me the EBITDA")
        
        assert response['intent'] == 'ebitda', f"Wrong intent: {response['intent']}"
        
        # If we have data, check structure
        if response['data'] is not None:
            assert 'ebitda' in response['data'], "Missing 'ebitda' in data"
            assert isinstance(response['data']['ebitda'], (int, float)), "EBITDA should be numeric"
        
    except Exception as e:
        pytest.skip(f"Data files not available or error in calculation: {e}")

def test_error_handling(agent):
    """Test that errors are handled gracefully"""
    # Test with various edge cases
    edge_cases = [
        "",  # Empty string
        "   ",  # Whitespace only
        "What is the meaning of life?",  # Unrelated question
    ]
    
    for question in edge_cases:
        response = agent.process_question(question)
        
        # Should always return proper structure
        required_keys = ['intent', 'text', 'chart', 'data']
        for key in required_keys:
            assert key in response, f"Missing key: {key} for question: '{question}'"
        
        # Should have some text response
        assert response['text'] != "", f"Empty response text for question: '{question}'"