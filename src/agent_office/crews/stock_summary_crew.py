from crewai import Crew, Process, Task

from agent_office.agents.email_agent import build_email_agent
from agent_office.agents.stock_agent import build_stock_agent
from agent_office.db.tracker import track_crew_run


class StockSummaryCrew:
    def run(self, tickers: list[str], recipients: list[str]) -> str:
        stock_agent = build_stock_agent()
        email_agent = build_email_agent()

        ticker_str = ", ".join(t.upper() for t in tickers)
        recipient_str = ", ".join(recipients)

        analyze_task = Task(
            description=(
                f"Analyze the following US stocks from an investment perspective: {ticker_str}\n\n"
                "For each ticker:\n"
                "  1. Call stock_data_fetcher to get the latest financial data\n"
                "  2. Assess valuation — is it cheap, fair, or expensive vs. sector norms?\n"
                "  3. Evaluate growth quality and profitability trend\n"
                "  4. Identify the top 2 catalysts and top 2 risks\n"
                "  5. Give a clear Buy / Hold / Sell recommendation with a 1-paragraph rationale\n\n"
                "Present results in a structured format with one section per stock, "
                "suitable for inclusion in an investor email."
            ),
            expected_output=(
                "A structured investment analysis for each ticker with valuation commentary, "
                "catalysts, risks, and a Buy/Hold/Sell recommendation."
            ),
            agent=stock_agent,
        )

        email_task = Task(
            description=(
                f"Send the stock investment analysis from the previous task via email to: {recipient_str}\n"
                f"Subject: US Stock Investment Summary — {ticker_str}\n"
                "Format the email professionally:\n"
                "  - Brief intro paragraph\n"
                "  - One clearly separated section per stock\n"
                "  - Closing disclaimer: 'This is AI-generated analysis, not financial advice.'"
            ),
            expected_output=f"Confirmation that the investment summary email was sent to {recipient_str}.",
            agent=email_agent,
            context=[analyze_task],
        )

        crew = Crew(
            agents=[stock_agent, email_agent],
            tasks=[analyze_task, email_task],
            process=Process.sequential,
            verbose=True,
        )
        result = track_crew_run(
            name=f"Stock summary: {ticker_str}",
            job_type="StockSummaryCrew",
            agents=["US Stock Investment Analyst", "Gmail Email Assistant"],
            crew=crew,
        )
        return str(result)
