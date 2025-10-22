# Test Cases - Seller Health API

## Endpoint
`GET /api/analytics/seller-health/:seller_id`

---

## Test Case 1: Valid Seller with Complete Data

### Request
```bash
curl -X GET "http://localhost:3000/api/analytics/seller-health/101" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK)
```json
{
  "seller_id": 101,
  "seller_name": "Example Seller Corp",
  "health_score": 78,
  "metrics": {
    "credit_utilization_rate": 0.65,
    "payment_reliability_score": 0.92,
    "lead_conversion_rate": 0.78,
    "wallet_health": {
      "current_balance": 450.50,
      "avg_weekly_change": 120.30,
      "trend": "improving"
    }
  },
  "risk_level": "low",
  "last_updated": "2025-10-21T14:30:00Z"
}
```

### Validation Checks
- ✅ Status code is 200
- ✅ Response contains all required fields
- ✅ `health_score` is between 0-100
- ✅ `credit_utilization_rate` is between 0-1
- ✅ `payment_reliability_score` is between 0-1
- ✅ `lead_conversion_rate` is between 0-1
- ✅ `risk_level` is one of: "low", "medium", "high"
- ✅ `trend` is either "improving" or "declining"

---

## Test Case 2: Valid Seller with High Risk

### Request
```bash
curl -X GET "http://localhost:3000/api/analytics/seller-health/250" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK)
```json
{
  "seller_id": 250,
  "seller_name": "High Risk Seller Ltd",
  "health_score": 32,
  "metrics": {
    "credit_utilization_rate": 0.95,
    "payment_reliability_score": 0.42,
    "lead_conversion_rate": 0.35,
    "wallet_health": {
      "current_balance": -250.75,
      "avg_weekly_change": -85.20,
      "trend": "declining"
    }
  },
  "risk_level": "high",
  "last_updated": "2025-10-21T14:30:00Z"
}
```

### Validation Checks
- ✅ Status code is 200
- ✅ `risk_level` is "high" (credit_utilization > 0.9 OR payment_reliability < 0.5)
- ✅ `health_score` is low (< 50)
- ✅ `trend` is "declining" (negative avg_weekly_change)
- ✅ Negative wallet balance is properly handled

---

## Test Case 3: Invalid Seller ID (Not Found)

### Request
```bash
curl -X GET "http://localhost:3000/api/analytics/seller-health/999999" \
  -H "Content-Type: application/json"
```

### Expected Response (404 Not Found)
```json
{
  "error": "Seller not found"
}
```

### Validation Checks
- ✅ Status code is 404
- ✅ Error message is clear and descriptive

---

## Test Case 4: Invalid Input (Non-Integer)

### Request
```bash
curl -X GET "http://localhost:3000/api/analytics/seller-health/abc" \
  -H "Content-Type: application/json"
```

### Expected Response (400 Bad Request)
```json
{
  "error": "seller_id must be an integer"
}
```

### Validation Checks
- ✅ Status code is 400
- ✅ Error message explains validation requirement

---

## Test Case 5: Seller with No Activity (Edge Case)

### Request
```bash
curl -X GET "http://localhost:3000/api/analytics/seller-health/50" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK)
```json
{
  "seller_id": 50,
  "seller_name": "Inactive Seller",
  "health_score": 20,
  "metrics": {
    "credit_utilization_rate": 0,
    "payment_reliability_score": 0,
    "lead_conversion_rate": 0,
    "wallet_health": {
      "current_balance": 0,
      "avg_weekly_change": 0,
      "trend": "declining"
    }
  },
  "risk_level": "low",
  "last_updated": "2025-10-21T14:30:00Z"
}
```

### Validation Checks
- ✅ Status code is 200
- ✅ All metrics default to 0 when no data exists
- ✅ No division by zero errors
- ✅ System handles NULL values gracefully with COALESCE

---

## Test Case 6: Seller with Medium Risk

### Request
```bash
curl -X GET "http://localhost:3000/api/analytics/seller-health/175" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK)
```json
{
  "seller_id": 175,
  "seller_name": "Medium Risk Seller",
  "health_score": 55,
  "metrics": {
    "credit_utilization_rate": 0.75,
    "payment_reliability_score": 0.65,
    "lead_conversion_rate": 0.60,
    "wallet_health": {
      "current_balance": 150.00,
      "avg_weekly_change": 25.50,
      "trend": "improving"
    }
  },
  "risk_level": "medium",
  "last_updated": "2025-10-21T14:30:00Z"
}
```

### Validation Checks
- ✅ Status code is 200
- ✅ `risk_level` is "medium" (credit_utilization > 0.7 OR payment_reliability < 0.7)
- ✅ Health score reflects medium performance (50-70 range)

---

## PowerShell Test Scripts

### Run All Tests
```powershell
# Test 1: Valid seller
curl.exe -X GET "http://localhost:3000/api/analytics/seller-health/101"

# Test 2: High risk seller
curl.exe -X GET "http://localhost:3000/api/analytics/seller-health/250"

# Test 3: Not found
curl.exe -X GET "http://localhost:3000/api/analytics/seller-health/999999"

# Test 4: Invalid input
curl.exe -X GET "http://localhost:3000/api/analytics/seller-health/abc"

# Test 5: No activity
curl.exe -X GET "http://localhost:3000/api/analytics/seller-health/50"

# Test 6: Medium risk
curl.exe -X GET "http://localhost:3000/api/analytics/seller-health/175"
```

---

## Performance Tests

### Load Test (10 concurrent requests)
```bash
# Using Apache Bench (if installed)
ab -n 100 -c 10 http://localhost:3000/api/analytics/seller-health/101

# Expected: < 500ms average response time
```

### Query Efficiency Verification
```sql
-- Verify indexes are being used
EXPLAIN QUERY PLAN
SELECT ... FROM sellers s
LEFT JOIN credits c ON s.seller_id = c.seller_id
WHERE s.seller_id = 101;

-- Should show: "SEARCH TABLE ... USING INDEX"
```

---

## Business Logic Validation

### Health Score Formula
```
health_score = payment_reliability × 40
             + lead_conversion × 30
             + (1 - credit_utilization) × 20
             + wallet_trend_bonus × 10
```

### Risk Level Logic
- **High**: `credit_utilization > 0.9 OR payment_reliability < 0.5`
- **Medium**: `credit_utilization > 0.7 OR payment_reliability < 0.7`
- **Low**: Otherwise

### Wallet Trend
- **Improving**: `avg_weekly_change > 0`
- **Declining**: `avg_weekly_change <= 0`

---

## Notes

1. **Single Query Requirement**: All metrics are computed in a single SQL query using CTEs
2. **Error Handling**: All edge cases (NULL values, division by zero) are handled with COALESCE and NULLIF
3. **Input Validation**: seller_id is validated as an integer before query execution
4. **Performance**: Query uses indexes on seller_id foreign keys for optimal performance
