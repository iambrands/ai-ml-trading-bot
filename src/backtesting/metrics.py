"""Performance metrics calculation."""

from datetime import datetime
from typing import Dict

import numpy as np

from ..trading.portfolio import Portfolio
from ..utils.logging import get_logger

logger = get_logger(__name__)


def calculate_metrics(
    portfolio: Portfolio,
    initial_capital: float,
    start_date: datetime,
    end_date: datetime,
) -> Dict[str, float]:
    """
    Calculate performance metrics.

    Args:
        portfolio: Portfolio instance
        initial_capital: Initial capital
        start_date: Start date
        end_date: End date

    Returns:
        Dictionary of metrics
    """
    final_value = portfolio.total_value
    total_return = (final_value - initial_capital) / initial_capital

    # Calculate time period in years
    days = (end_date - start_date).days
    years = days / 365.25

    # Annualized return
    if years > 0:
        annualized_return = (1 + total_return) ** (1 / years) - 1
    else:
        annualized_return = total_return

    # Sharpe ratio (simplified - would need risk-free rate)
    if portfolio.trades:
        returns = [t.pnl / initial_capital for t in portfolio.trades]
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
        else:
            sharpe_ratio = 0.0
    else:
        sharpe_ratio = 0.0

    # Win rate
    if portfolio.trades:
        winning_trades = [t for t in portfolio.trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(portfolio.trades)
    else:
        win_rate = 0.0

    # Profit factor
    if portfolio.trades:
        gross_profit = sum(t.pnl for t in portfolio.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in portfolio.trades if t.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    else:
        profit_factor = 0.0

    # Average trade return
    if portfolio.trades:
        avg_trade_return = np.mean([t.pnl / initial_capital for t in portfolio.trades])
    else:
        avg_trade_return = 0.0

    # Max drawdown (simplified)
    max_drawdown = 0.0
    if portfolio.trades:
        cumulative = initial_capital
        peak = initial_capital
        for trade in portfolio.trades:
            cumulative += trade.pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = (peak - cumulative) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

    metrics = {
        "initial_capital": initial_capital,
        "final_value": final_value,
        "total_return": total_return,
        "annualized_return": annualized_return,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "total_trades": len(portfolio.trades),
        "winning_trades": len([t for t in portfolio.trades if t.pnl > 0]),
        "losing_trades": len([t for t in portfolio.trades if t.pnl < 0]),
        "avg_trade_return": avg_trade_return,
        "realized_pnl": portfolio.realized_pnl,
        "unrealized_pnl": portfolio.unrealized_pnl,
        "total_pnl": portfolio.total_pnl,
    }

    return metrics

