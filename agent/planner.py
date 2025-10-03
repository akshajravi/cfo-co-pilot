import re
from typing import Dict, Any, Tuple, Optional
from .tools import FinanceDataTools

class CFOAgent:
    def __init__(self, data_path: str = "fixtures/"):
        self.data_path = data_path
        self.tools = FinanceDataTools(data_path)
    
    def classify_intent(self, question: str) -> str:
        """
        Classify user intent based on keyword matching
        """
        question_lower = question.lower()
        
        if "revenue" in question_lower and ("budget" in question_lower or "vs" in question_lower):
            return "revenue_vs_budget"
        elif "margin" in question_lower or "gross" in question_lower:
            return "gross_margin"
        elif "opex" in question_lower or "breakdown" in question_lower:
            return "opex_breakdown"
        elif "cash" in question_lower or "runway" in question_lower or "burn" in question_lower:
            return "cash_runway"
        elif "ebitda" in question_lower:
            return "ebitda"
        else:
            return "unknown"
    
    def extract_month_year(self, question: str) -> Tuple[Optional[int], int]:
        """
        Extract month and year from question text
        """
        month_mapping = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        question_lower = question.lower()
        month_num = None
        
        for month_name, num in month_mapping.items():
            if month_name in question_lower:
                month_num = num
                break
        
        year_match = re.search(r'20\d{2}', question)
        year = int(year_match.group()) if year_match else 2025
        
        return (month_num, year)
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process user question and route to appropriate tool method
        """
        try:
            intent = self.classify_intent(question)
            month_num, year = self.extract_month_year(question)
            
            if intent == "revenue_vs_budget":
                data = self.tools.get_revenue_vs_budget(month_num, year)
                chart = self.tools.create_revenue_chart(data)
                month_year = f"{month_num}/{year}" if month_num else f"{year}"
                text = f"Revenue {month_year}: Actual ${data['actual']:,.0f} vs Budget ${data['budget']:,.0f} (Variance: {data['variance_pct']:.1f}%)"
                
            elif intent == "gross_margin":
                data = self.tools.calculate_gross_margin(months=3)
                chart = self.tools.create_margin_trend_chart(data)
                text = f"Gross Margin: {data['avg_margin']:.1f}% average over last 3 months"
                
            elif intent == "opex_breakdown":
                data = self.tools.get_opex_breakdown(month_num, year)
                chart = self.tools.create_opex_breakdown_chart(data)
                month_year = f"{month_num}/{year}" if month_num else f"{year}"
                text = f"Opex breakdown for {month_year}"
                
            elif intent == "cash_runway":
                data = self.tools.get_cash_runway()
                chart = None
                text = f"Cash runway: {data['runway_months']:.1f} months (${data['cash_balance']:,.0f} balance, ${data['monthly_burn']:,.0f}/month burn)"
                
            elif intent == "ebitda":
                ebitda = self.tools.calculate_ebitda_proxy()
                data = {'ebitda': ebitda}
                chart = None
                text = f"EBITDA proxy: ${ebitda:,.0f}"
                
            else:
                data = None
                chart = None
                text = "I'm not sure how to help with that question. Please ask about revenue vs budget, gross margin, opex breakdown, cash runway, or EBITDA."
            
            return {
                'intent': intent,
                'text': text,
                'chart': chart,
                'data': data
            }
            
        except Exception as e:
            return {
                'intent': 'error',
                'text': f"Sorry, I encountered an error processing your question: {str(e)}",
                'chart': None,
                'data': None
            }