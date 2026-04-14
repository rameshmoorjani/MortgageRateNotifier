# 🏦 Setting Up FRED API for Real Mortgage Rates

Your system is currently using **mock rates** (which are realistic test data). To get **real Federal Reserve mortgage rates**, follow these steps:

---

## 📋 Step 1: Get Your Free FRED API Key

1. **Visit**: https://stlouisfed.org/apps/fred/
2. **Click**: "Create Account" (top right)
3. **Fill in**: Your email and password
4. **Verify**: Your email address
5. **Login**: To your FRED account
6. **Go to**: Account Settings → API Keys
7. **Copy**: Your API key (looks like: `abcdef1234567890abcdef1234567890`)

---

## 🔧 Step 2: Add API Key to Your Project

### **Option A: Using .env file** (Recommended)

1. Open `.env` file in your project root:
   ```
   c:\Users\rames\projects\MortgageRateNotifier\.env
   ```

2. Add this line:
   ```
   FRED_API_KEY=your_api_key_here
   ```

3. Replace `your_api_key_here` with your actual key from FRED

4. **Save the file**

### **Option B: Using .env.example as template**

1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` and replace:
   ```
   FRED_API_KEY=your-fred-api-key-here
   ```
   with your actual key

---

## 🧪 Step 3: Test the Integration

### **Restart the API**
```powershell
cd C:\Users\rames\projects\MortgageRateNotifier
c:\python314\python.exe -m uvicorn src.api_server:app --host 0.0.0.0 --port 8001
```

### **Test the endpoint**
Visit in browser:
```
http://localhost:8001/rates
```

### **Expected Response** (with real rates)
```json
{
  "source": "Federal Reserve FRED",
  "timestamp": "2026-04-09T20:15:00Z",
  "rates": {
    "30_year": 6.52,
    "15_year": 5.98,
    "5_1_arm": 6.12
  },
  "confidence": "high",
  "notice": "Updated weekly"
}
```

---

## 📊 What You'll Get

| Source | Data | Frequency | Confidence |
|--------|------|-----------|------------|
| **FRED** | Real Federal Reserve rates | Weekly | ✅ High |
| **Mock** | Realistic test rates | Always available | ⚠️ Low |

---

## 🔗 Endpoints with Real Rates

Once configured, all three endpoints will use real data:

1. **Current Rates**
   ```
   GET http://localhost:8001/rates
   ```

2. **Historical Rates** (30, 90, 365 days)
   ```
   GET http://localhost:8001/rates/historical?days=90
   ```

3. **Predicted Rates**
   ```
   POST http://localhost:8001/rates/predict?prediction_direction=DOWN&confidence=0.85
   ```

---

## ❓ Troubleshooting

### **Getting "Mock Data (APIs Unavailable)"?**
- ✅ FRED_API_KEY is not set in `.env`
- ✅ API server hasn't been restarted after adding the key
- ✅ API key is invalid or expired

**Solution**: 
1. Check `.env` file has correct key
2. Restart API server
3. Check FRED account still has valid API key

### **Getting API errors?**
- Verify your FRED API key is correct (no extra spaces)
- Check FRED account is still active (log in to FRED website)
- Ensure `.env` file is in the project root

---

## 📚 Additional Resources

- **FRED Documentation**: https://fred.stlouisfed.org/docs/api/
- **Mortgage Series IDs**: 
  - 30-year: MORTGAGE30US
  - 15-year: MORTGAGE15US
  - 5/1 ARM: MORTGAGE5US
- **Rate Update Schedule**: Freddie Mac updates Thursday mornings (FRED follows)

---

## 🎉 You're All Set!

Once configured, your system will:
- ✅ Fetch real mortgage rates from Federal Reserve
- ✅ Use rates for accurate refinancing decisions
- ✅ Provide historical rate trends
- ✅ Support rate direction predictions

**Time to configure**: ~5 minutes
**Your investment**: Free (FRED API is always free)

---

Let me know once you've added the API key and I can test it for you! 🚀
