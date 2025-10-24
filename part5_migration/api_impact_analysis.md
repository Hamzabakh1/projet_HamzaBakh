# API Impact Analysis: Multi-Currency Migration

## Executive Summary

**Migration:** Multi-Currency Support (Version 1.0.0)  
**Date:** October 22, 2025  
**Overall Impact:** Medium (Schema changes are backward-compatible, but APIs need updates to expose currency data)

### Impact Classification
- **Phase 1 (Migration):** No breaking changes, APIs continue to work
- **Phase 2 (API Updates):** Required updates to expose currency functionality
- **Phase 3 (Full Adoption):** All endpoints support multi-currency

---

## Affected API Endpoints

### 🔴 Critical Priority - Immediate Updates Required

#### 1. `POST /api/credits` - Create New Credit
**Current Behavior:**
```json
POST /api/credits
{
  "seller_id": 123,
  "amount": 5000.00,
  "due_date": "2025-12-31"
}
```

**Required Changes:**
```json
POST /api/credits
{
  "seller_id": 123,
  "amount": 5000.00,
  "currency": "SAR",  // NEW: Required field
  "due_date": "2025-12-31"
}
```

**Implementation:**
```javascript
router.post('/api/credits', (req, res) => {
  const { seller_id, amount, currency, due_date } = req.body;
  
  // Validation
  if (!currency || !['USD', 'EUR', 'SAR', 'AED'].includes(currency)) {
    return res.status(400).json({ 
      error: 'currency is required and must be one of: USD, EUR, SAR, AED' 
    });
  }
  
  // Get seller's preferred currency for validation
  const seller = db.get('SELECT preferred_currency FROM sellers WHERE seller_id = ?', [seller_id]);
  
  if (currency !== seller.preferred_currency) {
    console.warn(`Currency mismatch: seller prefers ${seller.preferred_currency}, credit in ${currency}`);
  }
  
  const query = `
    INSERT INTO credits (seller_id, amount, currency, issue_date, due_date, status)
    VALUES (?, ?, ?, date('now'), ?, 'New')
  `;
  
  db.run(query, [seller_id, amount, currency, due_date], function(err) {
    if (err) return res.status(500).json({ error: err.message });
    res.status(201).json({ credit_id: this.lastID, currency });
  });
});
```

**Migration Strategy:**
- Default to seller's `preferred_currency` if not provided (Phase 1)
- Make `currency` required field (Phase 2)
- Add validation to prevent currency mismatches

**Testing Requirements:**
- Test creating credits in all 4 currencies
- Test validation for invalid currency codes
- Test default currency behavior

---

#### 2. `GET /api/credits/:credit_id` - Get Credit Details
**Current Response:**
```json
{
  "credit_id": 101,
  "seller_id": 50,
  "amount": 5000.00,
  "status": "Approved",
  "issue_date": "2025-09-15",
  "due_date": "2025-12-15"
}
```

**Updated Response:**
```json
{
  "credit_id": 101,
  "seller_id": 50,
  "amount": 5000.00,
  "currency": "SAR",  // NEW
  "status": "Approved",
  "issue_date": "2025-09-15",
  "due_date": "2025-12-15",
  "converted_amounts": {  // NEW: For reporting
    "USD": 1333.33,
    "EUR": 1227.27,
    "AED": 4900.00
  }
}
```

**Implementation:**
```javascript
router.get('/api/credits/:credit_id', async (req, res) => {
  const creditId = req.params.credit_id;
  
  const query = `
    SELECT 
      c.*,
      s.preferred_currency
    FROM credits c
    JOIN sellers s ON c.seller_id = s.seller_id
    WHERE c.credit_id = ?
  `;
  
  db.get(query, [creditId], (err, credit) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!credit) return res.status(404).json({ error: 'Credit not found' });
    
    // Get exchange rates for conversion
    const ratesQuery = `
      SELECT to_currency, rate
      FROM latest_exchange_rates
      WHERE from_currency = ?
    `;
    
    db.all(ratesQuery, [credit.currency], (err, rates) => {
      const convertedAmounts = {};
      rates.forEach(r => {
        convertedAmounts[r.to_currency] = Math.round(credit.amount * r.rate * 100) / 100;
      });
      
      res.json({
        ...credit,
        converted_amounts: convertedAmounts
      });
    });
  });
});
```

---

### 🟡 High Priority - Update Within Sprint

#### 3. `GET /api/analytics/seller-health/:seller_id`
**Current Implementation:** Returns metrics in mixed currencies  
**Required Update:** Add currency normalization

**Updated Response:**
```json
{
  "seller_id": 123,
  "seller_name": "Acme Corp",
  "preferred_currency": "SAR",  // NEW
  "health_score": 85,
  "metrics": {
    "credit_utilization_rate": 0.65,
    "total_credits_issued": {  // NEW: Per currency
      "SAR": 50000.00,
      "USD_equivalent": 13333.33
    },
    "credit_limit": {  // NEW: In seller's currency
      "amount": 75000.00,
      "currency": "SAR"
    },
    "payment_reliability_score": 0.92,
    "lead_conversion_rate": 0.78,
    "wallet_health": {
      "current_balance": 450.50,
      "currency": "SAR",  // NEW
      "avg_weekly_change": 120.30,
      "trend": "improving"
    }
  },
  "risk_level": "low",
  "last_updated": "2025-10-21T14:30:00Z"
}
```

**Implementation Notes:**
- Calculate utilization in seller's preferred currency
- Convert all credits to common currency before aggregation
- Use `latest_exchange_rates` view

**SQL Query Update:**
```sql
WITH credit_stats AS (
  SELECT
    c.seller_id,
    -- Sum credits converted to seller's preferred currency
    SUM(c.amount * COALESCE(er.rate, 1.0)) AS total_issued_converted,
    s.credit_limit,
    s.preferred_currency,
    COUNT(CASE WHEN c.status = 'paid' THEN 1 END) * 1.0 / 
      NULLIF(COUNT(*), 0) AS payment_reliability
  FROM credits c
  JOIN sellers s ON c.seller_id = s.seller_id
  LEFT JOIN latest_exchange_rates er 
    ON c.currency = er.from_currency 
    AND s.preferred_currency = er.to_currency
  WHERE c.seller_id = ?
  GROUP BY c.seller_id
)
SELECT
  s.seller_id,
  s.seller_name,
  s.preferred_currency,
  cs.total_issued_converted / s.credit_limit AS credit_utilization_rate,
  -- ... rest of metrics
FROM sellers s
LEFT JOIN credit_stats cs ON s.seller_id = cs.seller_id
WHERE s.seller_id = ?
```

---

#### 4. `GET /api/dashboard/stats`
**Impact:** Aggregations must handle multiple currencies

**Current Response:**
```json
{
  "total_credits_issued": 4500000.00,
  "total_sales": 12500000.00,
  "active_sellers": 285
}
```

**Updated Response:**
```json
{
  "total_credits_issued": {
    "by_currency": {
      "USD": 2500000.00,
      "EUR": 150000.00,
      "SAR": 1500000.00,
      "AED": 350000.00
    },
    "total_usd_equivalent": 4500000.00  // All converted to USD
  },
  "total_sales": {
    "by_currency": {
      "USD": 7000000.00,
      "EUR": 400000.00,
      "SAR": 4000000.00,
      "AED": 1100000.00
    },
    "total_usd_equivalent": 12500000.00
  },
  "active_sellers": 285,
  "currency_distribution": {  // NEW
    "USD": 120,
    "EUR": 15,
    "SAR": 100,
    "AED": 50
  }
}
```

**Implementation:**
```javascript
router.get('/api/dashboard/stats', (req, res) => {
  const query = `
    WITH credit_summary AS (
      SELECT 
        c.currency,
        SUM(c.amount) AS total_amount,
        SUM(c.amount * COALESCE(er.rate, 1.0)) AS total_usd_equivalent
      FROM credits c
      LEFT JOIN latest_exchange_rates er 
        ON c.currency = er.from_currency 
        AND er.to_currency = 'USD'
      GROUP BY c.currency
    ),
    seller_currency AS (
      SELECT preferred_currency, COUNT(*) AS count
      FROM sellers
      GROUP BY preferred_currency
    )
    SELECT * FROM credit_summary
    UNION ALL
    SELECT * FROM seller_currency
  `;
  
  // Process results and build response...
});
```

---

### 🟢 Medium Priority - Next Sprint

#### 5. `GET /api/invoices/:invoice_id`
**Change:** Add `currency` field to response

#### 6. `POST /api/wallet/transactions`
**Change:** Accept `currency` in request body

#### 7. `GET /api/leads/:lead_id`
**Change:** Include `currency` for lead amount

#### 8. `GET /api/sellers/:seller_id`
**Change:** Include `preferred_currency` in response

---

## Database Query Patterns

### Pattern 1: Currency Conversion in Aggregations
```sql
-- Convert amounts to common currency (USD) for totals
SELECT 
  SUM(amount * COALESCE(
    (SELECT rate FROM latest_exchange_rates 
     WHERE from_currency = credits.currency 
     AND to_currency = 'USD'), 
    1.0
  )) AS total_usd_equivalent
FROM credits;
```

### Pattern 2: Multi-Currency Grouping
```sql
-- Show totals per currency + converted total
SELECT 
  currency,
  SUM(amount) AS total_in_currency,
  SUM(amount * COALESCE(er.rate, 1.0)) AS total_in_usd
FROM credits c
LEFT JOIN latest_exchange_rates er 
  ON c.currency = er.from_currency 
  AND er.to_currency = 'USD'
GROUP BY currency;
```

### Pattern 3: Seller-Specific Currency Context
```sql
-- Always use seller's preferred currency for calculations
SELECT 
  s.seller_id,
  s.preferred_currency,
  SUM(c.amount * COALESCE(er.rate, 1.0)) AS total_in_seller_currency
FROM sellers s
JOIN credits c ON s.seller_id = c.seller_id
LEFT JOIN latest_exchange_rates er 
  ON c.currency = er.from_currency 
  AND s.preferred_currency = er.to_currency
GROUP BY s.seller_id, s.preferred_currency;
```

---

## Frontend Impact

### Display Considerations

#### 1. Currency Formatting
```javascript
// Add currency-aware formatting
function formatAmount(amount, currency) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD'
  }).format(amount);
}

// Example usage
formatAmount(5000, 'SAR')  // "SAR 5,000.00"
```

#### 2. Currency Selector
```javascript
// Add to credit creation forms
<select name="currency" required>
  <option value="USD">USD - US Dollar</option>
  <option value="EUR">EUR - Euro</option>
  <option value="SAR">SAR - Saudi Riyal</option>
  <option value="AED">AED - UAE Dirham</option>
</select>
```

#### 3. Dashboard Filters
```javascript
// Add currency filter to analytics dashboards
<div class="currency-filter">
  <label>View amounts in:</label>
  <select id="display-currency">
    <option value="USD" selected>USD (Converted)</option>
    <option value="original">Original Currency</option>
  </select>
</div>
```

---

## Testing Strategy

### Unit Tests

```javascript
describe('Multi-Currency Credit API', () => {
  it('should create credit with specified currency', async () => {
    const response = await request(app)
      .post('/api/credits')
      .send({
        seller_id: 123,
        amount: 5000,
        currency: 'SAR',
        due_date: '2025-12-31'
      });
    
    expect(response.status).toBe(201);
    expect(response.body.currency).toBe('SAR');
  });
  
  it('should reject invalid currency code', async () => {
    const response = await request(app)
      .post('/api/credits')
      .send({
        seller_id: 123,
        amount: 5000,
        currency: 'GBP',  // Not supported
        due_date: '2025-12-31'
      });
    
    expect(response.status).toBe(400);
  });
  
  it('should convert amounts correctly', async () => {
    const response = await request(app)
      .get('/api/credits/101');
    
    expect(response.body.converted_amounts).toHaveProperty('USD');
    expect(response.body.converted_amounts).toHaveProperty('EUR');
  });
});
```

### Integration Tests

```javascript
describe('Seller Health with Multi-Currency', () => {
  it('should calculate utilization across multiple currencies', async () => {
    // Create credits in different currencies
    await createCredit(123, 1000, 'USD');
    await createCredit(123, 3750, 'SAR');  // Equivalent to $1000
    
    const health = await request(app)
      .get('/api/analytics/seller-health/123');
    
    // Should aggregate correctly
    expect(health.body.metrics.total_credits_issued.USD_equivalent).toBe(2000);
  });
});
```

### Manual Test Cases

1. **Create Credit in Each Currency**
   ```bash
   curl -X POST http://localhost:3000/api/credits \
     -H "Content-Type: application/json" \
     -d '{"seller_id": 123, "amount": 5000, "currency": "SAR", "due_date": "2025-12-31"}'
   ```

2. **Verify Currency Conversion**
   ```bash
   curl http://localhost:3000/api/credits/101
   # Check converted_amounts field
   ```

3. **Dashboard Aggregations**
   ```bash
   curl http://localhost:3000/api/dashboard/stats
   # Verify by_currency breakdown
   ```

---

## Performance Considerations

### Query Performance

**Before Multi-Currency:**
```sql
SELECT SUM(amount) FROM credits;  -- 2ms
```

**After Multi-Currency (with conversion):**
```sql
SELECT SUM(amount * rate) 
FROM credits c
JOIN latest_exchange_rates er ON c.currency = er.from_currency;
-- Estimated: 15-20ms
```

**Optimization Strategies:**
1. Add index on `credits(currency)` ✅ (Already in migration)
2. Cache exchange rates in application layer
3. Pre-calculate USD equivalents in materialized view

### Recommended Indexes (Already Created)
```sql
CREATE INDEX idx_credits_currency ON credits(currency);
CREATE INDEX idx_exchange_rates_currencies_date 
  ON exchange_rates(from_currency, to_currency, effective_date DESC);
```

---

## Backward Compatibility

### Maintaining Compatibility

**Strategy:** Gradual rollout with feature flags

```javascript
const ENABLE_MULTI_CURRENCY = process.env.MULTI_CURRENCY_ENABLED === 'true';

router.post('/api/credits', (req, res) => {
  let { seller_id, amount, currency, due_date } = req.body;
  
  if (!ENABLE_MULTI_CURRENCY) {
    currency = 'USD';  // Force USD in legacy mode
  } else if (!currency) {
    // Default to seller's preferred currency
    const seller = getSellerById(seller_id);
    currency = seller.preferred_currency;
  }
  
  // ... rest of implementation
});
```

### API Versioning (Recommended)

```javascript
// v1: Legacy, always returns USD
router.get('/api/v1/credits/:id', legacyCreditsHandler);

// v2: Multi-currency support
router.get('/api/v2/credits/:id', multiCurrencyCreditsHandler);
```

---

## Rollout Plan

### Phase 1: Schema Migration (Week 1)
- ✅ Run database migration
- ✅ All existing data defaults to USD
- ✅ APIs continue to work unchanged

### Phase 2: API Updates (Week 2-3)
- Update critical endpoints (POST /api/credits, GET /api/credits/:id)
- Add currency conversion logic
- Deploy with feature flag disabled

### Phase 3: Frontend Updates (Week 4)
- Add currency selectors to forms
- Update displays to show currency codes
- Add currency filters to dashboards

### Phase 4: Testing & Validation (Week 5)
- QA testing in staging environment
- Performance testing with currency conversions
- User acceptance testing

### Phase 5: Production Rollout (Week 6)
- Enable feature flag for 10% of traffic
- Monitor errors and performance
- Gradual rollout to 100%

---

## Monitoring & Alerts

### Key Metrics

1. **Currency Distribution**
   ```sql
   SELECT currency, COUNT(*) 
   FROM credits 
   WHERE created_at > date('now', '-7 days')
   GROUP BY currency;
   ```

2. **Conversion Errors**
   - Alert if no exchange rate found for currency pair
   - Monitor NULL values in converted amounts

3. **Performance**
   - Track query times for currency conversion queries
   - Alert if >500ms

4. **Data Quality**
   - Monitor for NULL currency values
   - Alert if currency codes outside ['USD','EUR','SAR','AED']

---

## Summary

| Endpoint | Impact | Updates Required | Priority | ETA |
|----------|--------|------------------|----------|-----|
| POST /api/credits | High | Add currency parameter | Critical | Sprint 1 |
| GET /api/credits/:id | Medium | Add currency to response | Critical | Sprint 1 |
| GET /api/analytics/seller-health/:id | High | Currency conversion logic | High | Sprint 1 |
| GET /api/dashboard/stats | High | Multi-currency aggregation | High | Sprint 2 |
| GET /api/invoices/:id | Low | Add currency field | Medium | Sprint 2 |
| POST /api/wallet/transactions | Low | Accept currency | Medium | Sprint 2 |
| GET /api/leads/:id | Low | Add currency field | Low | Sprint 3 |
| GET /api/sellers/:id | Low | Add preferred_currency | Low | Sprint 3 |

---

**Prepared by:** API Development Team  
**Reviewed by:** Technical Lead, Product Manager  
**Date:** October 21, 2025  
**Version:** 1.0.0
