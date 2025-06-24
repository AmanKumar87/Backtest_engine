# statistics.py
import pandas as pd
import numpy as np
try:
    import mplfinance as mpf
except ImportError:
    print("Warning: mplfinance is not installed. Advanced plotting will be disabled.")
    print("Please run: pip install mplfinance")
    mpf = None

class Statistics:
    """
    The Statistics class calculates a comprehensive set of performance metrics
    from a completed backtest.
    """
    def __init__(self, trades_log_path: str, portfolio, data_handler, risk_free_rate: float = 0.04):
        self.trades = pd.read_csv(trades_log_path, sep='|', index_col='Execution_Timestamp', parse_dates=True)
        self.portfolio = portfolio
        self.initial_capital = portfolio.initial_capital
        self.risk_free_rate = risk_free_rate
        self.full_price_data = data_handler.data
        self.equity_curve = self._calculate_equity_curve()
        self.returns = self.equity_curve['Total_Equity'].pct_change().dropna()

    def _calculate_equity_curve(self) -> pd.DataFrame:
        curve = self.full_price_data.copy()
        curve['Cash'] = self.initial_capital
        curve['Holdings_Value'] = 0.0
        holdings = 0.0
        for timestamp, trade in self.trades.iterrows():
            trade_time = timestamp.floor('D')
            trade_cost = (trade['Price'] * trade['Quantity']) + trade['Commission']
            if trade['Action'] == 'BUY':
                curve.loc[curve.index >= trade_time, 'Cash'] -= trade_cost
                holdings += trade['Quantity']
            elif trade['Action'] == 'SELL':
                curve.loc[curve.index >= trade_time, 'Cash'] += trade_cost
                holdings -= trade['Quantity']
            curve.loc[curve.index >= trade_time, 'Holdings_Qty'] = holdings
        if 'Holdings_Qty' not in curve.columns:
            curve['Holdings_Qty'] = 0.0
        curve['Holdings_Value'] = curve['Holdings_Qty'] * curve['Close']
        curve['Total_Equity'] = curve['Cash'] + curve['Holdings_Value']
        return curve

    def generate_report(self) -> dict:
        final_equity = self.equity_curve['Total_Equity'].iloc[-1]
        total_pnl = final_equity - self.initial_capital
        buy_hold_return = (self.full_price_data['Close'].iloc[-1] / self.full_price_data['Close'].iloc[0] - 1) * self.initial_capital
        gross_profit, gross_loss, winning_trades, losing_trades = 0.0, 0.0, 0, 0
        profit_factor = float('inf') if gross_loss == 0 else abs(gross_profit / gross_loss)
        total_closed_trades = winning_trades + losing_trades
        pct_profitable = (winning_trades / total_closed_trades) * 100 if total_closed_trades > 0 else 0
        max_dd_val, max_dd_pct = self.calculate_max_drawdown()
        
        report = {
            "Ending Equity": f"{final_equity:,.2f}", "Total Net P/L": f"{total_pnl:,.2f}",
            "Profitability": f"{(total_pnl / self.initial_capital) * 100:.2f}%",
            "Buy & Hold Return": f"{buy_hold_return:,.2f}", "--- Risk Metrics ---": "---",
            "Sharpe Ratio": f"{self.calculate_sharpe_ratio():.2f}",
            "Sortino Ratio": f"{self.calculate_sortino_ratio():.2f}",
            "Max Drawdown": f"{max_dd_val:,.2f} ({max_dd_pct:.2%})",
            "--- Trade Stats (Closed Trades) ---": "---", "Total Closed Trades": total_closed_trades,
            "Profit Factor": f"{profit_factor:.2f}", "Percent Profitable": f"{pct_profitable:.2f}%",
        }
        return report

    def calculate_max_drawdown(self) -> tuple[float, float]:
        roll_max = self.equity_curve['Total_Equity'].cummax()
        drawdown = self.equity_curve['Total_Equity'] - roll_max
        max_drawdown_val = drawdown.min()
        max_dd_pct = (max_drawdown_val / roll_max[drawdown.idxmin()]) if roll_max[drawdown.idxmin()] != 0 else 0
        return max_drawdown_val, max_dd_pct

    def calculate_sharpe_ratio(self) -> float:
        if self.returns.empty or self.returns.std() == 0: return 0.0
        excess_returns = self.returns - (self.risk_free_rate / 252)
        return np.sqrt(252) * (excess_returns.mean() / excess_returns.std())

    def calculate_sortino_ratio(self) -> float:
        if self.returns.empty: return 0.0
        downside_returns = self.returns[self.returns < 0]
        if downside_returns.empty or downside_returns.std() == 0: return 0.0
        expected_return = self.returns.mean()
        downside_std = downside_returns.std()
        return np.sqrt(252) * (expected_return - (self.risk_free_rate / 252)) / downside_std
        
    def plot_advanced_charts(self, output_path: str, title: str = 'Backtest Analysis'):
        if mpf is None: return

        # Start with the equity curve plot, which is always present
        addplots = [
            mpf.make_addplot(self.equity_curve['Total_Equity'], panel=1, color='royalblue', ylabel='Equity (₹)')
        ]

        # --- CONDITIONAL PLOTTING FOR BUY MARKERS ---
        buy_trades = self.trades[self.trades['Action'] == 'BUY']
        if not buy_trades.empty:
            buy_markers = pd.Series(np.nan, index=self.full_price_data.index)
            buy_markers.loc[buy_trades.index] = self.full_price_data.loc[buy_trades.index]['Low'] * 0.98
            addplots.append(mpf.make_addplot(buy_markers, type='scatter', marker='^', color='lime', markersize=100, panel=0))

        # --- CONDITIONAL PLOTTING FOR SELL MARKERS ---
        sell_trades = self.trades[self.trades['Action'] == 'SELL']
        if not sell_trades.empty:
            sell_markers = pd.Series(np.nan, index=self.full_price_data.index)
            sell_markers.loc[sell_trades.index] = self.full_price_data.loc[sell_trades.index]['High'] * 1.02
            addplots.append(mpf.make_addplot(sell_markers, type='scatter', marker='v', color='red', markersize=100, panel=0))
        
        mpf.plot(
            self.full_price_data, type='candle', style='yahoo', title=title,
            ylabel='Price (₹)', addplot=addplots, panel_ratios=(3, 1),
            figscale=1.5, warn_too_much_data=len(self.full_price_data) + 1,
            savefig=dict(fname=output_path, dpi=300)
        )
        print(f"Advanced analysis chart saved to: {output_path}")
    # statistics.py (add this new method inside the Statistics class)

    def plot_interactive_ohlc_chart(self, output_path: str, title: str = 'Interactive Trade Chart'):
        """
        Plots an interactive OHLC candlestick chart with trade markers using Plotly.
        """
        try:
            import plotly.graph_objects as go

            fig = go.Figure(data=[go.Candlestick(x=self.full_price_data.index,
                                               open=self.full_price_data['Open'],
                                               high=self.full_price_data['High'],
                                               low=self.full_price_data['Low'],
                                               close=self.full_price_data['Close'],
                                               name='Price')])

            buy_trades = self.trades[self.trades['Action'] == 'BUY']
            sell_trades = self.trades[self.trades['Action'] == 'SELL']

            if not buy_trades.empty:
                fig.add_trace(go.Scatter(
                    x=buy_trades.index, y=buy_trades['Price'], mode='markers',
                    marker=dict(symbol='triangle-up', color='lime', size=12, line=dict(width=1, color='black')),
                    name='Buy Trade'
                ))

            if not sell_trades.empty:
                fig.add_trace(go.Scatter(
                    x=sell_trades.index, y=sell_trades['Price'], mode='markers',
                    marker=dict(symbol='triangle-down', color='red', size=12, line=dict(width=1, color='black')),
                    name='Sell Trade'
                ))

            fig.update_layout(
                title=title, xaxis_title='Date', yaxis_title='Price (₹)',
                xaxis_rangeslider_visible=True, template='plotly_dark'
            )

            fig.write_html(output_path)
            print(f"Interactive OHLC chart saved to: {output_path}")

        except ImportError:
            print("\nWarning: plotly is not installed. Skipping interactive plot generation.")
            print("Please run: pip install plotly")