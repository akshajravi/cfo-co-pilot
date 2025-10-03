# CFO Copilot 📊

An AI-powered financial assistant that answers CFO questions with interactive charts and real-time analysis. Ask questions in natural language and get instant insights from your financial data.

## Features

- **Natural Language Queries** - Ask questions like "What was June revenue vs budget?"
- **Interactive Charts** - Automatic visualization with Plotly charts
- **Key Financial Metrics** - Revenue analysis, Gross Margin trends, EBITDA calculations, Cash Runway, OpEx breakdown
- **Real-time Analysis** - Direct analysis from CSV data files
- **Multi-currency Support** - Automatic USD conversion with FX rates
- **Intent Classification** - Smart routing to appropriate financial analysis tools

## Quick Start

### 1. Clone & Install
```bash
git clone <your-repo>
cd cfo-copilot
pip install -r requirements.txt
```

### 2. Prepare Data Files
Place your CSV files in the `fixtures/` directory:
- `actuals.csv` - Actual financial data
- `budget.csv` - Budget data  
- `cash.csv` - Cash flow data
- `fx.csv` - Foreign exchange rates

### 3. Run the Application
```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`

## Data Format

Your CSV files should follow this structure:

**actuals.csv & budget.csv:**
```
month,entity,account_category,amount,currency
2025-06,ParentCo,Revenue,125000,USD
2025-06,EMEA,COGS,45000,EUR
```

**cash.csv:**
```
month,entity,cash_usd
2025-06,Consolidated,850000
```

**fx.csv:**
```
month,currency,rate_to_usd
2025-06,EUR,1.08
2025-06,USD,1.00
```

**Account Categories:**
- `Revenue`
- `COGS` 
- `Opex:Marketing`
- `Opex:Sales`
- `Opex:R&D`
- `Opex:Admin`

## Sample Questions

Try these example questions:

- "What was June 2025 revenue vs budget in USD?"
- "Show gross margin trend for the last 3 months"
- "Break down opex by category for June"
- "What is our cash runway right now?"
- "Calculate EBITDA for this quarter"

## Project Structure

```
cfo-copilot/
├── README.md
├── requirements.txt
├── app.py                    # Streamlit web interface
├── agent/
│   ├── __init__.py
│   ├── planner.py           # CFOAgent orchestration
│   └── tools.py             # FinanceDataTools calculations
├── fixtures/                 # CSV data files
│   └── .gitkeep
├── tests/
│   ├── __init__.py
│   └── test_agent.py        # Pytest unit tests
└── scripts/
    └── download_data.py     # Data utilities
```

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Sample Data Generation
```bash
python scripts/download_data.py --sample
```

### Dependencies
- **pandas** - Data manipulation
- **streamlit** - Web interface
- **plotly** - Interactive charts
- **pytest** - Unit testing

## Architecture

1. **CFOAgent** (`agent/planner.py`) - Main orchestrator that:
   - Classifies user intent from natural language
   - Extracts time periods (month/year)
   - Routes to appropriate analysis tools

2. **FinanceDataTools** (`agent/tools.py`) - Financial calculations:
   - Revenue vs budget analysis
   - Gross margin calculations
   - OpEx breakdown
   - Cash runway modeling
   - EBITDA proxy calculations
   - Chart generation

3. **Streamlit App** (`app.py`) - Web interface with:
   - Chat-style Q&A interface
   - Sample question buttons
   - Interactive chart display
   - Data status monitoring
