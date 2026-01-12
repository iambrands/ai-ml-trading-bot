# 🚀 Top 3 Features - Usage Guide

## 1. Real-Time Alerts & Notifications

### Create an Alert (Webhook)
```bash
curl -X POST https://your-domain.com/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "SIGNAL",
    "alert_rule": {
      "min_edge": 0.08,
      "min_confidence": 0.65,
      "min_signal_strength": "MEDIUM"
    },
    "notification_method": "WEBHOOK",
    "notification_target": "https://your-webhook-url.com/alerts",
    "enabled": true
  }'
```

### Create an Alert (Email - when implemented)
```bash
curl -X POST https://your-domain.com/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "SIGNAL",
    "alert_rule": {"min_edge": 0.10},
    "notification_method": "EMAIL",
    "notification_target": "your-email@example.com",
    "enabled": true
  }'
```

### List All Alerts
```bash
curl https://your-domain.com/alerts
```

### Get Alert History
```bash
curl https://your-domain.com/alerts/1/history
```

### Enable/Disable Alert
```bash
curl -X PUT https://your-domain.com/alerts/1/enable
curl -X PUT https://your-domain.com/alerts/1/disable
```

**How it works:** When a signal is generated that matches your alert rules, the system automatically sends a notification to your configured webhook/email.

---

## 2. Paper Trading Mode

### Create a Paper Trade
```bash
curl -X POST https://your-domain.com/paper-trading/trades \
  -H "Content-Type: application/json" \
  -d '{
    "signal_id": 123,
    "entry_price": 0.55,
    "size": 100.0
  }'
```

### Get Paper Trades
```bash
# All paper trades
curl https://your-domain.com/paper-trading/trades

# Only open trades
curl https://your-domain.com/paper-trading/trades?status=OPEN

# Only closed trades
curl https://your-domain.com/paper-trading/trades?status=CLOSED
```

### Close a Paper Trade
```bash
curl -X PUT "https://your-domain.com/paper-trading/trades/456/close?exit_price=0.60"
```

### Get Paper Portfolio
```bash
# Latest snapshot
curl https://your-domain.com/paper-trading/portfolio

# All snapshots
curl https://your-domain.com/paper-trading/portfolio/snapshots
```

**How it works:** Paper trades are tracked separately from real trades. You can test strategies risk-free with virtual capital.

---

## 3. Advanced Analytics Dashboard

### Get Dashboard Summary (All Metrics)
```bash
curl https://your-domain.com/analytics/dashboard-summary?days=30
```

### Individual Metrics

**Prediction Accuracy**
```bash
curl https://your-domain.com/analytics/prediction-accuracy?days=30
```

**Trade Performance**
```bash
# Real trades
curl https://your-domain.com/analytics/trade-performance?days=30

# Paper trades
curl https://your-domain.com/analytics/trade-performance?days=30&paper_trading=true
```

**Edge Distribution**
```bash
curl https://your-domain.com/analytics/edge-distribution?days=30
```

**Portfolio Metrics**
```bash
# Real portfolio
curl https://your-domain.com/analytics/portfolio-metrics?days=30

# Paper portfolio
curl https://your-domain.com/analytics/portfolio-metrics?days=30&paper_trading=true
```

**Signal Strength Performance**
```bash
curl https://your-domain.com/analytics/signal-strength-performance?days=30
```

**Response Example:**
```json
{
  "prediction_accuracy": {
    "total": 150,
    "correct": 95,
    "accuracy": 0.6333,
    "brier_score": 0.2156
  },
  "trade_performance": {
    "total_trades": 45,
    "win_rate": 0.6222,
    "total_pnl": 1250.50,
    "profit_factor": 1.85
  },
  "portfolio_metrics": {
    "total_return": 0.1250,
    "sharpe_ratio": 1.65,
    "max_drawdown": 0.0850
  }
}
```

---

## Database Migration

Before using these features, run the migration:

```bash
# Using Railway CLI
railway connect postgres
\i src/database/migrations/add_alerts_and_paper_trading.sql

# Or using psql directly
psql $DATABASE_URL -f src/database/migrations/add_alerts_and_paper_trading.sql
```

---

## Integration Notes

- **Alerts** are automatically triggered when signals are generated (if alerts are configured)
- **Paper Trading** works alongside real trading - both are tracked separately
- **Analytics** work for both real and paper trading (use `paper_trading=true` parameter)
- All features are **non-disruptive** - existing functionality continues to work

---

## Example Workflow

1. **Set up alerts** for high-confidence signals
2. **Generate predictions** (existing endpoint)
3. **Receive alerts** when signals match your rules
4. **Test with paper trading** before using real capital
5. **Monitor analytics** to track performance
6. **Compare paper vs real** performance

---

*All endpoints are documented in the FastAPI docs at `/docs`*

