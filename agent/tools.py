import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

class FinanceDataTools:
    def __init__(self, data_path: str = "fixtures/"):
        self.data_path = data_path
        self.load_data()
    
    def load_data(self):
        """Load all data from Excel file"""
        try:
            excel_path = f"{self.data_path}data.xlsx"
            
            # Read all sheets
            self.actuals_df = pd.read_excel(excel_path, sheet_name='actuals')
            self.budget_df = pd.read_excel(excel_path, sheet_name='budget')
            self.fx_df = pd.read_excel(excel_path, sheet_name='fx')
            self.cash_df = pd.read_excel(excel_path, sheet_name='cash')
            
            # Clean column names (strip whitespace)
            for df in [self.actuals_df, self.budget_df, self.fx_df, self.cash_df]:
                df.columns = df.columns.str.strip()
            
            # Parse month columns as datetime
            self.actuals_df['month'] = pd.to_datetime(self.actuals_df['month'])
            self.budget_df['month'] = pd.to_datetime(self.budget_df['month'])
            self.cash_df['month'] = pd.to_datetime(self.cash_df['month'])
            self.fx_df['month'] = pd.to_datetime(self.fx_df['month'])
            
            print("✅ Data loaded successfully from data.xlsx!")
            print(f"  Actuals: {self.actuals_df.shape[0]} rows")
            print(f"  Budget: {self.budget_df.shape[0]} rows")
            print(f"  Cash: {self.cash_df.shape[0]} rows")
            print(f"  FX: {self.fx_df.shape[0]} rows")
            
        except FileNotFoundError:
            print(f"❌ Error: data.xlsx not found in {self.data_path}")
            print("Please download data.xlsx and place it in the fixtures/ folder")
            raise
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise
    
    def _convert_to_usd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert amounts to USD using FX rates"""
        try:
            df_with_fx = df.merge(self.fx_df, on=['month', 'currency'], how='left')
            df_with_fx['rate_to_usd'] = df_with_fx['rate_to_usd'].fillna(1.0)  # USD default
            df_with_fx['amount_usd'] = df_with_fx['amount'] * df_with_fx['rate_to_usd']
            return df_with_fx
        except Exception as e:
            print(f"Error converting to USD: {e}")
            df['amount_usd'] = df.get('amount', 0)
            return df
    
    def get_revenue_vs_budget(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, float]:
        """Get revenue vs budget comparison"""
        try:
            # Filter for Revenue
            revenue_actual = self.actuals_df[self.actuals_df['account_category'] == 'Revenue'].copy()
            revenue_budget = self.budget_df[self.budget_df['account_category'] == 'Revenue'].copy()
            
            # Filter by month/year if provided
            if month and year:
                target_date = f"{year}-{month:02d}"
                revenue_actual = revenue_actual[revenue_actual['month'].dt.strftime('%Y-%m') == target_date]
                revenue_budget = revenue_budget[revenue_budget['month'].dt.strftime('%Y-%m') == target_date]
            elif year:
                revenue_actual = revenue_actual[revenue_actual['month'].dt.year == year]
                revenue_budget = revenue_budget[revenue_budget['month'].dt.year == year]
            
            # Convert to USD
            revenue_actual = self._convert_to_usd(revenue_actual)
            revenue_budget = self._convert_to_usd(revenue_budget)
            
            actual_total = revenue_actual['amount_usd'].sum()
            budget_total = revenue_budget['amount_usd'].sum()
            variance = actual_total - budget_total
            variance_pct = (variance / budget_total * 100) if budget_total != 0 else 0
            
            return {
                'actual': actual_total,
                'budget': budget_total,
                'variance': variance,
                'variance_pct': variance_pct
            }
        except Exception as e:
            print(f"Error in get_revenue_vs_budget: {e}")
            return {'actual': 0, 'budget': 0, 'variance': 0, 'variance_pct': 0}
    
    def calculate_gross_margin(self, months: int = 3) -> Dict[str, Any]:
        """Calculate gross margin for last N months"""
        try:
            # Get last N months
            latest_months = self.actuals_df['month'].nlargest(months).sort_values()
            
            margins = []
            month_labels = []
            
            for month in latest_months:
                month_data = self.actuals_df[self.actuals_df['month'] == month]
                
                revenue = month_data[month_data['account_category'] == 'Revenue']
                cogs = month_data[month_data['account_category'] == 'COGS']
                
                revenue = self._convert_to_usd(revenue)
                cogs = self._convert_to_usd(cogs)
                
                revenue_total = revenue['amount_usd'].sum()
                cogs_total = cogs['amount_usd'].sum()
                
                margin = (revenue_total - cogs_total) / revenue_total if revenue_total != 0 else 0
                margins.append(margin * 100)  # Convert to percentage
                month_labels.append(month.strftime('%Y-%m'))
            
            avg_margin = np.mean(margins) if margins else 0
            
            return {
                'margins': margins,
                'months': month_labels,
                'avg_margin': avg_margin
            }
        except Exception as e:
            print(f"Error in calculate_gross_margin: {e}")
            return {'margins': [], 'months': [], 'avg_margin': 0}
    
    def get_opex_breakdown(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, float]:
        """Get OpEx breakdown by category"""
        try:
            opex_data = self.actuals_df[self.actuals_df['account_category'].str.startswith('Opex:')].copy()
            
            # Filter by month/year if provided
            if month and year:
                target_date = f"{year}-{month:02d}"
                opex_data = opex_data[opex_data['month'].dt.strftime('%Y-%m') == target_date]
            elif year:
                opex_data = opex_data[opex_data['month'].dt.year == year]
            
            # Convert to USD
            opex_data = self._convert_to_usd(opex_data)
            
            # Group by category and sum
            breakdown = opex_data.groupby('account_category')['amount_usd'].sum().to_dict()
            
            return breakdown
        except Exception as e:
            print(f"Error in get_opex_breakdown: {e}")
            return {}
    
    def calculate_ebitda_proxy(self) -> float:
        """Calculate EBITDA proxy (Revenue - COGS - OpEx)"""
        try:
            # Get all data and convert to USD
            all_data = self._convert_to_usd(self.actuals_df)
            
            revenue = all_data[all_data['account_category'] == 'Revenue']['amount_usd'].sum()
            cogs = all_data[all_data['account_category'] == 'COGS']['amount_usd'].sum()
            opex = all_data[all_data['account_category'].str.startswith('Opex:')]['amount_usd'].sum()
            
            ebitda = revenue - cogs - opex
            return ebitda
        except Exception as e:
            print(f"Error in calculate_ebitda_proxy: {e}")
            return 0
    
    def get_cash_runway(self) -> Dict[str, float]:
        """Calculate cash runway based on last 3 months"""
        try:
            # Get last 4 months to calculate 3-month burn
            latest_cash = self.cash_df.nlargest(4, 'month').sort_values('month')
            
            if len(latest_cash) < 4:
                return {'cash_balance': 0, 'monthly_burn': 0, 'runway_months': 0}
            
            cash_start = latest_cash.iloc[0]['cash_usd']
            cash_end = latest_cash.iloc[-1]['cash_usd']
            
            monthly_burn = (cash_start - cash_end) / 3
            current_cash = cash_end
            
            runway_months = current_cash / monthly_burn if monthly_burn > 0 else float('inf')
            
            return {
                'cash_balance': current_cash,
                'monthly_burn': monthly_burn,
                'runway_months': runway_months
            }
        except Exception as e:
            print(f"Error in get_cash_runway: {e}")
            return {'cash_balance': 0, 'monthly_burn': 0, 'runway_months': 0}
    
    def create_revenue_chart(self, data: Dict[str, float]) -> go.Figure:
        """Create revenue vs budget bar chart"""
        try:
            fig = go.Figure(data=[
                go.Bar(name='Actual', x=['Revenue'], y=[data['actual']]),
                go.Bar(name='Budget', x=['Revenue'], y=[data['budget']])
            ])
            
            fig.update_layout(
                title='Revenue vs Budget',
                xaxis_title='Category',
                yaxis_title='Amount (USD)',
                barmode='group'
            )
            
            return fig
        except Exception as e:
            print(f"Error creating revenue chart: {e}")
            return go.Figure()
    
    def create_margin_trend_chart(self, data: Dict[str, Any]) -> go.Figure:
        """Create margin trend line chart"""
        try:
            fig = go.Figure(data=go.Scatter(
                x=data['months'],
                y=data['margins'],
                mode='lines+markers',
                name='Gross Margin %'
            ))
            
            fig.update_layout(
                title='Gross Margin Trend',
                xaxis_title='Month',
                yaxis_title='Margin (%)'
            )
            
            return fig
        except Exception as e:
            print(f"Error creating margin chart: {e}")
            return go.Figure()
    
    def create_opex_breakdown_chart(self, data: Dict[str, float]) -> go.Figure:
        """Create OpEx breakdown bar chart"""
        try:
            categories = list(data.keys())
            amounts = list(data.values())
            
            fig = go.Figure(data=[
                go.Bar(x=categories, y=amounts)
            ])
            
            fig.update_layout(
                title='OpEx Breakdown',
                xaxis_title='Category',
                yaxis_title='Amount (USD)'
            )
            
            return fig
        except Exception as e:
            print(f"Error creating opex chart: {e}")
            return go.Figure()
    
    # Wrapper methods for CFOAgent compatibility
    def revenue_vs_budget(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        data = self.get_revenue_vs_budget(month, year)
        chart = self.create_revenue_chart(data)
        return {
            'text': f"Revenue: ${data['actual']:,.0f} vs Budget: ${data['budget']:,.0f} (Variance: {data['variance_pct']:.1f}%)",
            'chart': chart,
            'data': data
        }
    
    def gross_margin(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        data = self.calculate_gross_margin()
        chart = self.create_margin_trend_chart(data)
        return {
            'text': f"Average gross margin: {data['avg_margin']:.1f}%",
            'chart': chart,
            'data': data
        }
    
    def opex_breakdown(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        data = self.get_opex_breakdown(month, year)
        chart = self.create_opex_breakdown_chart(data)
        total_opex = sum(data.values())
        return {
            'text': f"Total OpEx: ${total_opex:,.0f}",
            'chart': chart,
            'data': data
        }
    
    def cash_runway(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        data = self.get_cash_runway()
        return {
            'text': f"Cash balance: ${data['cash_balance']:,.0f}, Monthly burn: ${data['monthly_burn']:,.0f}, Runway: {data['runway_months']:.1f} months",
            'chart': None,
            'data': data
        }
    
    def ebitda(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        data = self.calculate_ebitda_proxy()
        return {
            'text': f"EBITDA proxy: ${data:,.0f}",
            'chart': None,
            'data': {'ebitda': data}
        }