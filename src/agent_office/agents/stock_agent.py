from agent_office.agents.base import build_agent
from agent_office.tools.stock_tool import StockDataTool


def build_stock_agent():
    return build_agent(
        role="US Stock Investment Analyst",
        goal=(
            "Analyze US stocks using real financial data and provide clear, actionable "
            "investment insights including valuation assessment, key risks, and a "
            "Buy / Hold / Sell recommendation"
        ),
        backstory=(
            "You are a seasoned equity analyst with deep expertise in fundamental analysis, "
            "valuation modeling, and market dynamics. You cut through noise to deliver "
            "concise, data-driven investment theses. You always ground your views in the "
            "numbers and compare metrics to sector norms."
        ),
        tools=[StockDataTool()],
    )
