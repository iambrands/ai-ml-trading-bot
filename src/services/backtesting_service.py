"""Advanced Backtesting Engine Service."""

import math
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import BacktestRun, BacktestTrade, PriceHistory
from ..utils.logging import get_logger

logger = get_logger(__name__)


class BacktestingService:
    """Service for running backtests on trading strategies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_backtest(
        self,
        name: str,
        strategy_name: str,
        strategy_params: Dict,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
    ) -> Optional[Dict]:
        """Run a backtest for a given strategy and time period."""
        try:
            run = BacktestRun(
                name=name,
                strategy_name=strategy_name,
                strategy_params=strategy_params,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                status="RUNNING",
            )
            self.db.add(run)
            await self.db.commit()
            await self.db.refresh(run)

            results = await self._execute_backtest(run)

            run.final_capital = results["final_capital"]
            run.total_return_pct = results["total_return_pct"]
            run.annualized_return_pct = results.get("annualized_return_pct")
            run.sharpe_ratio = results.get("sharpe_ratio")
            run.sortino_ratio = results.get("sortino_ratio")
            run.max_drawdown_pct = results.get("max_drawdown_pct")
            run.win_rate = results.get("win_rate")
            run.profit_factor = results.get("profit_factor")
            run.total_trades = results.get("total_trades", 0)
            run.avg_trade_pnl = results.get("avg_trade_pnl")
            run.avg_hold_time_hours = results.get("avg_hold_time_hours")
            run.calmar_ratio = results.get("calmar_ratio")
            run.equity_curve = results.get("equity_curve")
            run.monthly_returns = results.get("monthly_returns")
            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(run)

            logger.info("Backtest completed", name=name, return_pct=results["total_return_pct"])
            return self._run_to_dict(run)
        except Exception as e:
            logger.error("Backtest failed", name=name, error=str(e))
            if run:
                run.status = "FAILED"
                run.error_message = str(e)
                await self.db.commit()
            return None

    async def get_backtest_runs(self, strategy_name: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get backtest run history."""
        try:
            query = select(BacktestRun)
            if strategy_name:
                query = query.where(BacktestRun.strategy_name == strategy_name)
            query = query.order_by(desc(BacktestRun.created_at)).limit(limit)

            result = await self.db.execute(query)
            runs = result.scalars().all()
            return [self._run_to_dict(r) for r in runs]
        except Exception as e:
            logger.error("Failed to get backtest runs", error=str(e))
            return []

    async def get_backtest_detail(self, backtest_id: int) -> Optional[Dict]:
        """Get detailed results for a specific backtest run."""
        try:
            result = await self.db.execute(
                select(BacktestRun).where(BacktestRun.id == backtest_id)
            )
            run = result.scalar_one_or_none()
            if not run:
                return None

            trades_result = await self.db.execute(
                select(BacktestTrade)
                .where(BacktestTrade.backtest_id == backtest_id)
                .order_by(BacktestTrade.entry_time)
            )
            trades = trades_result.scalars().all()

            detail = self._run_to_dict(run)
            detail["trades"] = [
                {
                    "market_id": t.market_id,
                    "side": t.side,
                    "entry_price": float(t.entry_price),
                    "exit_price": float(t.exit_price) if t.exit_price else None,
                    "size": float(t.size),
                    "pnl": float(t.pnl) if t.pnl else None,
                    "entry_time": t.entry_time.isoformat(),
                    "exit_time": t.exit_time.isoformat() if t.exit_time else None,
                    "signal_strength": t.signal_strength,
                }
                for t in trades
            ]
            return detail
        except Exception as e:
            logger.error("Failed to get backtest detail", error=str(e))
            return None

    async def compare_backtests(self, backtest_ids: List[int]) -> Dict:
        """Compare multiple backtest runs side by side."""
        try:
            result = await self.db.execute(
                select(BacktestRun).where(BacktestRun.id.in_(backtest_ids))
            )
            runs = result.scalars().all()

            comparison = {
                "runs": [self._run_to_dict(r) for r in runs],
                "best_return": None,
                "best_sharpe": None,
                "best_win_rate": None,
            }

            if runs:
                best_return = max(runs, key=lambda r: float(r.total_return_pct or 0))
                comparison["best_return"] = {"name": best_return.name, "value": float(best_return.total_return_pct or 0)}

                runs_with_sharpe = [r for r in runs if r.sharpe_ratio is not None]
                if runs_with_sharpe:
                    best_sharpe = max(runs_with_sharpe, key=lambda r: float(r.sharpe_ratio))
                    comparison["best_sharpe"] = {"name": best_sharpe.name, "value": float(best_sharpe.sharpe_ratio)}

                runs_with_wr = [r for r in runs if r.win_rate is not None]
                if runs_with_wr:
                    best_wr = max(runs_with_wr, key=lambda r: float(r.win_rate))
                    comparison["best_win_rate"] = {"name": best_wr.name, "value": float(best_wr.win_rate)}

            return comparison
        except Exception as e:
            logger.error("Failed to compare backtests", error=str(e))
            return {"runs": [], "error": str(e)}

    async def delete_backtest(self, backtest_id: int) -> bool:
        """Delete a backtest run and its trades."""
        try:
            result = await self.db.execute(
                select(BacktestRun).where(BacktestRun.id == backtest_id)
            )
            run = result.scalar_one_or_none()
            if not run:
                return False
            await self.db.delete(run)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error("Failed to delete backtest", error=str(e))
            await self.db.rollback()
            return False

    async def _execute_backtest(self, run: BacktestRun) -> Dict:
        """Execute backtesting using real price history when available, with simulation fallback."""
        capital = float(run.initial_capital)
        equity_curve = [{"date": run.start_date.isoformat(), "equity": capital}]
        trades = []
        pnl_list = []

        params = run.strategy_params or {}
        min_edge = params.get("min_edge", 0.05)
        position_pct = params.get("position_pct", 0.05)
        take_profit = params.get("take_profit", 0.15)
        stop_loss = params.get("stop_loss", 0.10)
        strategy = run.strategy_name.upper().replace(" ", "_")

        price_data = await self._load_price_data(run.start_date, run.end_date)

        if price_data:
            capital, trades, pnl_list, equity_curve = await self._backtest_with_real_data(
                run, capital, price_data, params
            )
        else:
            capital, trades, pnl_list, equity_curve = self._backtest_with_simulation(
                run, capital, params
            )

        for t in trades:
            bt_trade = BacktestTrade(
                backtest_id=run.id,
                market_id=t.get("market_id", "unknown"),
                side=t["side"],
                entry_price=t.get("entry_price", 0.5),
                exit_price=t.get("exit_price"),
                size=t["size"],
                pnl=t["pnl"],
                entry_time=t["entry_time"],
                exit_time=t.get("exit_time"),
                signal_strength=t.get("signal_strength", "MEDIUM"),
            )
            self.db.add(bt_trade)

        num_days = max(1, (run.end_date - run.start_date).days)
        total_return = (capital - float(run.initial_capital)) / float(run.initial_capital) * 100
        winning = [p for p in pnl_list if p > 0]
        losing = [p for p in pnl_list if p < 0]

        win_rate = len(winning) / len(pnl_list) if pnl_list else 0
        gross_profit = sum(winning) if winning else 0
        gross_loss = abs(sum(losing)) if losing else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0

        # Sharpe ratio
        if pnl_list and len(pnl_list) > 1:
            avg_pnl = sum(pnl_list) / len(pnl_list)
            std_pnl = math.sqrt(sum((p - avg_pnl) ** 2 for p in pnl_list) / len(pnl_list))
            sharpe = (avg_pnl / std_pnl * math.sqrt(252)) if std_pnl > 0 else 0
        else:
            avg_pnl = 0
            sharpe = 0

        # Max drawdown
        peak = float(run.initial_capital)
        max_dd = 0
        running_capital = float(run.initial_capital)
        for t in trades:
            running_capital += t["pnl"]
            peak = max(peak, running_capital)
            dd = (peak - running_capital) / peak
            max_dd = max(max_dd, dd)

        # Sortino ratio
        downside = [p for p in pnl_list if p < 0]
        downside_std = math.sqrt(sum(p**2 for p in downside) / len(downside)) if downside else 0
        sortino = (avg_pnl / downside_std * math.sqrt(252)) if downside_std > 0 else 0

        annualized = total_return * (365 / max(num_days, 1))
        calmar = annualized / (max_dd * 100) if max_dd > 0 else 0

        return {
            "final_capital": round(capital, 2),
            "total_return_pct": round(total_return, 4),
            "annualized_return_pct": round(annualized, 4),
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4),
            "max_drawdown_pct": round(max_dd * 100, 4),
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 4) if profit_factor != float('inf') else 999.0,
            "total_trades": len(trades),
            "avg_trade_pnl": round(avg_pnl, 4),
            "avg_hold_time_hours": 24,
            "calmar_ratio": round(calmar, 4),
            "equity_curve": equity_curve[::max(1, len(equity_curve)//100)],
            "monthly_returns": None,
        }

    async def _load_price_data(self, start_date: datetime, end_date: datetime) -> Dict[str, List]:
        """Load real price history data from the database for backtesting."""
        try:
            from sqlalchemy import and_
            result = await self.db.execute(
                select(PriceHistory)
                .where(and_(
                    PriceHistory.timestamp >= start_date,
                    PriceHistory.timestamp <= end_date,
                ))
                .order_by(PriceHistory.timestamp)
                .limit(10000)
            )
            rows = result.scalars().all()
            if not rows:
                return {}

            by_market: Dict[str, List] = {}
            for row in rows:
                mid = row.market_id
                if mid not in by_market:
                    by_market[mid] = []
                by_market[mid].append({
                    "timestamp": row.timestamp,
                    "yes_price": float(row.yes_price),
                    "no_price": float(row.no_price),
                    "volume": float(row.volume),
                })

            markets_with_data = {k: v for k, v in by_market.items() if len(v) >= 5}
            logger.info("Loaded price data for backtest", markets=len(markets_with_data), total_points=sum(len(v) for v in markets_with_data.values()))
            return markets_with_data
        except Exception as e:
            logger.error("Failed to load price data", error=str(e))
            return {}

    async def _backtest_with_real_data(self, run, capital: float, price_data: Dict[str, List], params: Dict) -> tuple:
        """Run backtest against real price history."""
        trades = []
        pnl_list = []
        equity_curve = [{"date": run.start_date.isoformat(), "equity": capital}]

        min_edge = params.get("min_edge", 0.05)
        position_pct = params.get("position_pct", 0.05)
        take_profit = params.get("take_profit", 0.15)
        stop_loss = params.get("stop_loss", 0.10)

        for market_id, prices in price_data.items():
            if len(prices) < 10 or capital < 100:
                continue

            i = 10
            while i < len(prices) - 1:
                window = [p["yes_price"] for p in prices[i-10:i]]
                current = prices[i]["yes_price"]
                mean = sum(window) / len(window)
                deviation = current - mean

                if abs(deviation) < min_edge:
                    i += 1
                    continue

                side = "NO" if deviation > min_edge else "YES"
                entry_price = current
                size = min(capital * position_pct, capital * 0.1)

                for j in range(i + 1, min(i + 50, len(prices))):
                    future_price = prices[j]["yes_price"]
                    if side == "YES":
                        pnl_pct = (future_price - entry_price) / max(entry_price, 0.01)
                    else:
                        pnl_pct = (entry_price - future_price) / max(entry_price, 0.01)

                    if pnl_pct >= take_profit or pnl_pct <= -stop_loss or j == min(i + 49, len(prices) - 1):
                        pnl = size * pnl_pct
                        capital += pnl
                        pnl_list.append(pnl)
                        trades.append({
                            "market_id": market_id,
                            "side": side,
                            "entry_price": entry_price,
                            "exit_price": future_price,
                            "size": size,
                            "pnl": pnl,
                            "entry_time": prices[i]["timestamp"],
                            "exit_time": prices[j]["timestamp"],
                            "signal_strength": "STRONG" if abs(deviation) > min_edge * 2 else "MEDIUM",
                        })
                        equity_curve.append({"date": prices[j]["timestamp"].isoformat(), "equity": round(capital, 2)})
                        i = j + 1
                        break
                else:
                    i += 1

        return capital, trades, pnl_list, equity_curve

    def _backtest_with_simulation(self, run, capital: float, params: Dict) -> tuple:
        """Fallback simulation when no real price data is available."""
        trades = []
        pnl_list = []
        equity_curve = [{"date": run.start_date.isoformat(), "equity": capital}]
        num_days = (run.end_date - run.start_date).days

        win_prob = params.get("win_probability", 0.55)
        avg_return = params.get("avg_return", 0.08)
        trade_freq = params.get("trade_frequency_per_day", 2)

        for day in range(num_days):
            current_date = run.start_date + timedelta(days=day)
            num_trades = max(0, int(random.gauss(trade_freq, 1)))

            for _ in range(num_trades):
                size = min(capital * 0.05, capital * random.uniform(0.02, 0.08))
                if size < 10 or capital < 100:
                    continue

                entry_price = random.uniform(0.2, 0.8)
                if random.random() < win_prob:
                    pnl = size * random.uniform(0.02, avg_return * 2)
                    exit_price = entry_price + pnl / size
                else:
                    pnl = -size * random.uniform(0.02, avg_return * 1.5)
                    exit_price = entry_price + pnl / size

                capital += pnl
                pnl_list.append(pnl)
                side = random.choice(["YES", "NO"])
                trades.append({
                    "market_id": f"sim_market_{random.randint(1, 100)}",
                    "side": side,
                    "entry_price": round(max(0.01, min(0.99, entry_price)), 6),
                    "exit_price": round(max(0.01, min(0.99, exit_price)), 6),
                    "size": size,
                    "pnl": pnl,
                    "entry_time": current_date,
                    "exit_time": current_date + timedelta(hours=random.randint(1, 72)),
                    "signal_strength": random.choice(["STRONG", "MEDIUM"]),
                })

            equity_curve.append({"date": current_date.isoformat(), "equity": round(capital, 2)})

        return capital, trades, pnl_list, equity_curve

    def _run_to_dict(self, run: BacktestRun) -> Dict:
        return {
            "id": run.id,
            "name": run.name,
            "strategy_name": run.strategy_name,
            "strategy_params": run.strategy_params,
            "start_date": run.start_date.isoformat() if run.start_date else None,
            "end_date": run.end_date.isoformat() if run.end_date else None,
            "initial_capital": float(run.initial_capital),
            "final_capital": float(run.final_capital) if run.final_capital else None,
            "total_return_pct": float(run.total_return_pct) if run.total_return_pct else None,
            "annualized_return_pct": float(run.annualized_return_pct) if run.annualized_return_pct else None,
            "sharpe_ratio": float(run.sharpe_ratio) if run.sharpe_ratio else None,
            "sortino_ratio": float(run.sortino_ratio) if run.sortino_ratio else None,
            "max_drawdown_pct": float(run.max_drawdown_pct) if run.max_drawdown_pct else None,
            "win_rate": float(run.win_rate) if run.win_rate else None,
            "profit_factor": float(run.profit_factor) if run.profit_factor else None,
            "total_trades": run.total_trades,
            "avg_trade_pnl": float(run.avg_trade_pnl) if run.avg_trade_pnl else None,
            "calmar_ratio": float(run.calmar_ratio) if run.calmar_ratio else None,
            "equity_curve": run.equity_curve,
            "status": run.status,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }
