import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def _pct(val) -> str:
    return f"{val * 100:.1f}%" if val is not None else "N/A"


def _usd(val) -> str:
    return f"${val:,.2f}" if val is not None else "N/A"


def _fmt(val) -> str:
    return str(round(val, 2)) if val is not None else "N/A"


def _market_cap(val) -> str:
    if not val:
        return "N/A"
    if val >= 1e12:
        return f"${val / 1e12:.2f}T"
    if val >= 1e9:
        return f"${val / 1e9:.2f}B"
    return f"${val / 1e6:.0f}M"


class StockDataInput(BaseModel):
    ticker: str = Field(description="Stock ticker symbol, e.g. AAPL, MSFT, NVDA")


class StockDataTool(BaseTool):
    name: str = "stock_data_fetcher"
    description: str = (
        "Fetch real-time stock data and key financial metrics for a given US ticker symbol. "
        "Returns price, valuation ratios, growth metrics, analyst ratings, and 3-month performance."
    )
    args_schema: type[BaseModel] = StockDataInput

    def _run(self, ticker: str) -> str:
        symbol = ticker.upper().strip()
        stock = yf.Ticker(symbol)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return f"Could not fetch data for ticker '{symbol}'. Check the symbol and try again."

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        hist = stock.history(period="3mo")
        price_change_3m = "N/A"
        if not hist.empty and len(hist) >= 2:
            start = hist["Close"].iloc[0]
            end = hist["Close"].iloc[-1]
            price_change_3m = f"{(end - start) / start * 100:.1f}%"

        lines = [
            f"=== {symbol} — {info.get('longName', symbol)} ===",
            f"Sector: {info.get('sector', 'N/A')} | Industry: {info.get('industry', 'N/A')}",
            "",
            "── Price ──",
            f"Current Price:      {_usd(price)}",
            f"52W High:           {_usd(info.get('fiftyTwoWeekHigh'))}",
            f"52W Low:            {_usd(info.get('fiftyTwoWeekLow'))}",
            f"3M Price Change:    {price_change_3m}",
            f"50-Day MA:          {_usd(info.get('fiftyDayAverage'))}",
            f"200-Day MA:         {_usd(info.get('twoHundredDayAverage'))}",
            "",
            "── Valuation ──",
            f"Market Cap:         {_market_cap(info.get('marketCap'))}",
            f"Trailing P/E:       {_fmt(info.get('trailingPE'))}",
            f"Forward P/E:        {_fmt(info.get('forwardPE'))}",
            f"PEG Ratio:          {_fmt(info.get('pegRatio'))}",
            f"Price/Book:         {_fmt(info.get('priceToBook'))}",
            f"EV/EBITDA:          {_fmt(info.get('enterpriseToEbitda'))}",
            "",
            "── Growth & Profitability ──",
            f"Revenue Growth YoY: {_pct(info.get('revenueGrowth'))}",
            f"Earnings Growth:    {_pct(info.get('earningsGrowth'))}",
            f"Gross Margin:       {_pct(info.get('grossMargins'))}",
            f"Profit Margin:      {_pct(info.get('profitMargins'))}",
            f"Return on Equity:   {_pct(info.get('returnOnEquity'))}",
            "",
            "── Analyst Consensus ──",
            f"Recommendation:     {info.get('recommendationKey', 'N/A').upper()}",
            f"Target Price (mean):{_usd(info.get('targetMeanPrice'))}",
            f"# of Analysts:      {info.get('numberOfAnalystOpinions', 'N/A')}",
            "",
            "── Income ──",
            f"Dividend Yield:     {_pct(info.get('dividendYield'))}",
            f"Beta:               {_fmt(info.get('beta'))}",
            f"Short % of Float:   {_pct(info.get('shortPercentOfFloat'))}",
        ]
        return "\n".join(lines)
