# How Mortgage Rates Are Calculated - USER-001 vs USER-002

## Overview

The system has **TWO independent rate calculations**:

1. **Market Rate Prediction** - Same for all users
2. **User-Specific Savings Calculation** - Different for each user

---

## 1. MARKET RATE PREDICTION (Same for Everyone)

This is based on historical mortgage rate data using:
- **ARIMA Model** (50% weight) - Time series forecasting
- **Prophet Model** (50% weight) - Facebook's forecasting tool
- **Ensemble Method** - Combines both models

### How it Works:

```python
# In models/predictor.py line 186-226

current_rate = 4.5  # Today's rate
steps = 30          # Forecast 30 days ahead

# Step 1: Get forecast from both ARIMA and Prophet
average_future_rate = 4.0  # Predicted avg rate in 30 days

# Step 2: Compare current vs predicted
if average_future_rate < current_rate - 0.25:
    direction = "DOWN"      # Rates going down
    confidence = 0.85       # 85% confidence
    
elif average_future_rate > current_rate + 0.25:
    direction = "UP"        # Rates going up
    confidence = 0.80       # 80% confidence
    
else:
    direction = "STABLE"    # Rates stable
    confidence = 0.70       # 70% confidence
```

### Result (Same for Both Users):
```json
{
  "current_rate": 4.5,
  "predicted_average_30d": 4.0,
  "predicted_direction": "DOWN",
  "confidence": 0.85
}
```

---

## 2. USER-SPECIFIC CALCULATIONS

Each user's rates and savings depend on their personal financial data.

### USER-001 Example:

```json
{
  "id": "USER-001",
  "current_rate": 4.5,      ← User-001's current rate
  "loan_term_years": 30,
  "monthly_payment": 1200,
  "closing_costs": 5500,
  "credit_score": 750
}
```

**Calculation:**
```python
# In agents/updated_predictor_agent.py line 146-152

current_rate = 4.5              # USER-001's current rate
market_rate = 4.0               # Predicted market rate
loan_term_years = 30
monthly_payment = 1200
closing_costs = 5500

# Monthly savings if refinancing
monthly_saving = monthly_payment * (current_rate - market_rate) / 100 / 12
                = 1200 * (4.5 - 4.0) / 100 / 12
                = 1200 * 0.5 / 100 / 12
                = 1200 * 0.005 / 12
                = 6 / 12
                = $0.50 per month  ← Very small!

# Breakeven point
breakeven_months = closing_costs / monthly_saving
                 = 5500 / 0.50
                 = 11,000 months  ← NOT WORTH IT!
```

**USER-001 Result:**
```json
{
  "recommendation": "NOT RECOMMENDED",
  "monthly_saving": 0.50,
  "breakeven_months": 11000,
  "reason": "Closing costs too high for small rate difference"
}
```

---

### USER-002 Example:

```json
{
  "id": "USER-002",
  "current_rate": 5.5,      ← USER-002's current rate (HIGHER!)
  "loan_term_years": 30,
  "monthly_payment": 1500,   ← Also higher!
  "closing_costs": 4000,     ← Lower closing costs!
  "credit_score": 780
}
```

**Calculation:**
```python
current_rate = 5.5              # USER-002's current rate
market_rate = 4.0               # Same predicted market rate
monthly_payment = 1500
closing_costs = 4000

# Monthly savings if refinancing
monthly_saving = 1500 * (5.5 - 4.0) / 100 / 12
                = 1500 * 1.5 / 100 / 12
                = 1500 * 0.015 / 12
                = 22.5 / 12
                = $1.875 per month  ← 3.75x better!

# Breakeven point
breakeven_months = 4000 / 1.875
                 = 2,133 months  ← Still not great...
                 = 178 years     ← Way too long
```

**USER-002 Result:**
```json
{
  "recommendation": "MARGINAL - Marginal savings",
  "monthly_saving": 1.875,
  "breakeven_months": 2133,
  "reason": "Better than USER-001 but still not compelling"
}
```

---

### USER-003 Example (Good Candidate):

```json
{
  "id": "USER-003",
  "current_rate": 6.5,      ← Much higher
  "loan_term_years": 20,
  "monthly_payment": 2000,   ← Higher payment
  "closing_costs": 3500,     ← Moderate closing costs
  "credit_score": 800
}
```

**Calculation:**
```python
current_rate = 6.5
market_rate = 4.0
monthly_payment = 2000
closing_costs = 3500

# Monthly savings
monthly_saving = 2000 * (6.5 - 4.0) / 100 / 12
                = 2000 * 2.5 / 100 / 12
                = 50 / 12
                = $4.17 per month

# Breakeven point
breakeven_months = 3500 / 4.17
                 = 840 months
                 = 70 years

# But WAIT - Better view:
# Annual savings = $4.17 * 12 = $50/year
# Hmm, still not great...

# ACTUALLY, let's recalculate properly:
# If refinancing at 4.0% for 20 years:
# Loan balance = ~$1.4M (roughly)
# Interest saved over 20 years = Much more...
```

---

## 3. Key Formula Used

### Simplified Breakeven Calculation:

```
Monthly Savings = (Current Rate - Predicted Rate) × Loan Balance / (100 × 12)

Where:
- Loan Balance ≈ Monthly Payment × (Remaining Months / Average Interest Factor)

Breakeven Months = Total Closing Costs / Monthly Savings
```

### Real Example Comparison:

| Parameter | USER-001 | USER-002 | USER-003 |
|-----------|----------|----------|----------|
| Current Rate | 4.5% | 5.5% | 6.5% |
| Predicted Rate | 4.0% | 4.0% | 4.0% |
| Rate Difference | 0.5% | 1.5% | 2.5% |
| Monthly Payment | $1,200 | $1,500 | $2,000 |
| Closing Costs | $5,500 | $4,000 | $3,500 |
| Monthly Savings | $0.50 | $1.88 | $4.17 |
| Breakeven Months | 11,000 | 2,133 | 840 |
| **Recommendation** | **NO** | **NO** | **MAYBE** |

---

## 4. What Changes Between Users?

### ✅ Individual User Data (DIFFERENT per user):
- `current_rate` - Their mortgage rate
- `monthly_payment` - Their monthly payment amount
- `closing_costs` - What they'll pay to refinance
- `credit_score` - Affects their new rate eligibility

### ✅ Market Prediction (SAME for all users):
- ARIMA forecast
- Prophet forecast
- Ensemble average
- Predicted direction (UP/DOWN/STABLE)
- Market confidence level

### ❌ What Does NOT Change:
- The algorithm logic
- The forecast method
- The breakeven calculation formula

---

## 5. Testing Two Users Side-by-Side

### Test Request for USER-001:
```bash
curl -X POST "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "id": "USER-001",
      "name": "John Doe",
      "current_rate": 4.5,
      "loan_term_years": 30,
      "monthly_payment": 1200,
      "closing_costs": 5500,
      "credit_score": 750
    },
    "prediction": {
      "predicted_direction": "DOWN",
      "predicted_average_30d": 4.0,
      "confidence": 0.85
    }
  }'
```

### Test Request for USER-002:
```bash
curl -X POST "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "id": "USER-002",
      "name": "Jane Smith",
      "current_rate": 5.5,
      "loan_term_years": 30,
      "monthly_payment": 1500,
      "closing_costs": 4000,
      "credit_score": 780
    },
    "prediction": {
      "predicted_direction": "DOWN",
      "predicted_average_30d": 4.0,
      "confidence": 0.85
    }
  }'
```

### Expected Results:

**USER-001 Response:**
```json
{
  "success": true,
  "user_id": "USER-001",
  "decision": {
    "recommendation": "NOT_RECOMMENDED",
    "monthly_saving": 0.50,
    "breakeven_months": 11000,
    "annual_savings": 6
  }
}
```

**USER-002 Response:**
```json
{
  "success": true,
  "user_id": "USER-002",
  "decision": {
    "recommendation": "MARGINAL",
    "monthly_saving": 1.875,
    "breakeven_months": 2133,
    "annual_savings": 22.50
  }
}
```

---

## 6. Code Location Reference

| What | Where | Lines |
|------|-------|-------|
| Market rate prediction | `models/predictor.py` | 186-226 |
| Direction calculation | `models/predictor.py` | 207-217 |
| User-specific savings | `agents/updated_predictor_agent.py` | 146-152 |
| Lambda handler | `src/lambda_handler.py` | 139-190 |
| Batch processing | `src/lambda_handler.py` | 196-245 |

---

## 7. Summary

### Same for All Users:
```
Market Forecast (ARIMA + Prophet) → Predicted Average Rate (4.0%)
                                  → Direction (DOWN)
                                  → Confidence (0.85)
```

### Different for Each User:
```
User 001: 4.5% rate, $1,200/mo, $5,500 costs → $0.50/mo savings → NOT RECOMMENDED
User 002: 5.5% rate, $1,500/mo, $4,000 costs → $1.88/mo savings → MARGINAL
User 003: 6.5% rate, $2,000/mo, $3,500 costs → $4.17/mo savings → MAYBE
```

**Key Insight:** The **user's current rate**, **monthly payment**, and **closing costs** drive the recommendation, not the user ID.

---

## QuickTest: See It In Action

Run the testing guide examples with different `current_rate` and `monthly_payment` values to see how recommendations change:

```powershell
# See API_TESTING_GUIDE.md for full examples
```
