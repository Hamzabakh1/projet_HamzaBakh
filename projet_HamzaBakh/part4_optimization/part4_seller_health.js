// ============================================================================
// PART 4.2 — DATABASE OPTIMIZATION: SELLER HEALTH ANALYTICS ENDPOINT
//
// Candidate Name:  HAMZA BAKH
// Date:            22 Oct 2025
// Time Spent:      30 min (Analytics Endpoint)
// ============================================================================
// This module provides seller health scoring and risk assessment analytics.
//
// Objective:
// Implement comprehensive seller health metrics in single optimized query.
// Calculate credit utilization, payment reliability, lead conversion, and
// wallet health with proper risk classification.
//
// Metrics Calculated:
// 1. Credit Utilization Rate: Issued Credits / Credit Limit
// 2. Payment Reliability: Paid Credits / Total Credits (excl. Cancelled)
// 3. Lead Conversion Rate: Confirmed Leads / Total Leads
// 4. Wallet Health Trend: Improving/Declining based on avg_weekly_change
// 5. Risk Level: High/Medium/Low based on utilization & reliability
// 6. Health Score: Weighted average (0-100) of all metrics
//
// How to run:
//   curl http://localhost:3000/api/analytics/seller-health/123
// ============================================================================

const express = require('express');
const router = express.Router();

// ============================================================================
// ENDPOINT: GET /api/analytics/seller-health/:seller_id
// ============================================================================
// Returns comprehensive seller health metrics for risk assessment.
//
// Parameters:
//   seller_id (integer): Numeric ID of seller to analyze
//
// Response (200 OK):
// {
//   "seller_id": 123,
//   "seller_name": "Tech Solutions",
//   "health_score": 85,
//   "metrics": {
//     "credit_utilization_rate": 0.65,
//     "payment_reliability_score": 0.92,
//     "lead_conversion_rate": 0.78,
//     "wallet_health": {
//       "current_balance": 450.50,
//       "avg_weekly_change": 120.30,
//       "trend": "improving"
//     }
//   },
//   "risk_level": "low",
//   "last_updated": "2025-10-24T10:30:00Z"
// }
//
// Error Responses:
//   400 Bad Request: seller_id not integer
//   404 Not Found: Seller doesn't exist in database
//   500 Server Error: Database query failed
// ============================================================================
router.get('/api/analytics/seller-health/:seller_id', (req, res) => {
  const db = req.app.locals.db;
  const sellerId = parseInt(req.params.seller_id);

  // ========================================================================
  // INPUT VALIDATION: Ensure seller_id is valid integer
  // ========================================================================
  if (isNaN(sellerId)) {
    return res.status(400).json({ 
      error: 'Invalid input',
      message: 'seller_id must be an integer',
      received: req.params.seller_id
    });
  }

  // ========================================================================
  // OPTIMIZED QUERY: Single query with CTEs to avoid N+1 problem
  // ========================================================================
  // This query calculates all health metrics in one pass:
  // - credit_stats CTE: Aggregates credit metrics by seller
  // - lead_stats CTE: Calculates lead conversion rate
  // - wallet_stats CTE: Aggregates wallet transaction health
  // - Final SELECT: Joins all CTEs and calculates weighted health score
  //
  // Index Usage:
  // - idx_credits_seller_id: Fast credit stats lookup
  // - idx_leads_seller_id: Fast lead stats lookup
  // - idx_wallet_transactions_seller_id: Fast wallet lookup
  // ========================================================================
  const query = `
    -- PART 1: Calculate credit metrics (utilization, payment reliability)
    WITH credit_stats AS (
      SELECT
        c.seller_id,
        SUM(c.amount) AS total_issued,
        MAX(s.credit_limit) AS credit_limit,
        SUM(CASE WHEN c.status = 'paid' THEN 1 ELSE 0 END) * 1.0 / 
          NULLIF(SUM(CASE WHEN c.status != 'cancelled' THEN 1 ELSE 0 END), 0) AS payment_reliability
      FROM credits c
      JOIN sellers s ON c.seller_id = s.seller_id
      WHERE c.seller_id = ?
      GROUP BY c.seller_id
    ),
    
    -- PART 2: Calculate lead conversion metrics
    lead_stats AS (
      SELECT
        seller_id,
        SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) * 1.0 / 
          NULLIF(COUNT(lead_id), 0) AS lead_conversion
      FROM leads
      WHERE seller_id = ?
      GROUP BY seller_id
    ),
    
    -- PART 3: Calculate wallet health metrics
    wallet_stats AS (
      SELECT
        seller_id,
        SUM(amount) AS current_balance,
        AVG(amount) AS avg_weekly_change
      FROM wallet_transactions
      WHERE seller_id = ?
      GROUP BY seller_id
    )
    
    -- PART 4: Join all metrics and calculate final health score
    -- Health Score Formula (0-100):
    --   (payment_reliability × 40) +
    --   (lead_conversion × 30) +
    --   ((1 - utilization_rate) × 20) +
    --   (wallet_improving_bonus × 10)
    SELECT
      s.seller_id,
      s.seller_name,
      ROUND((COALESCE(cs.payment_reliability, 0) * 40 +
             COALESCE(ls.lead_conversion, 0) * 30 +
             (1 - COALESCE(cs.total_issued / NULLIF(cs.credit_limit, 0), 0)) * 20 +
             CASE WHEN COALESCE(ws.avg_weekly_change, 0) > 0 THEN 10 ELSE 0 END), 0) AS health_score,
      COALESCE(cs.total_issued, 0) * 1.0 / NULLIF(cs.credit_limit, 0) AS credit_utilization_rate,
      COALESCE(cs.payment_reliability, 0) AS payment_reliability_score,
      COALESCE(ls.lead_conversion, 0) AS lead_conversion_rate,
      COALESCE(ws.current_balance, 0) AS current_balance,
      COALESCE(ws.avg_weekly_change, 0) AS avg_weekly_change,
      CASE WHEN COALESCE(ws.avg_weekly_change, 0) > 0 THEN 'improving' ELSE 'declining' END AS trend,
      CASE
        WHEN (COALESCE(cs.total_issued, 0) * 1.0 / NULLIF(cs.credit_limit, 1)) > 0.9 OR COALESCE(cs.payment_reliability, 1) < 0.5 THEN 'high'
        WHEN (COALESCE(cs.total_issued, 0) * 1.0 / NULLIF(cs.credit_limit, 1)) > 0.7 OR COALESCE(cs.payment_reliability, 1) < 0.7 THEN 'medium'
        ELSE 'low'
      END AS risk_level,
      DATETIME('now') AS last_updated
    FROM sellers s
    LEFT JOIN credit_stats cs ON s.seller_id = cs.seller_id
    LEFT JOIN lead_stats ls ON s.seller_id = ls.seller_id
    LEFT JOIN wallet_stats ws ON s.seller_id = ws.seller_id
    WHERE s.seller_id = ?;
  `;

  // ========================================================================
  // EXECUTION: Query database with proper error handling
  // ========================================================================
  db.get(query, [sellerId, sellerId, sellerId, sellerId], (err, row) => {
    if (err) {
      console.error('Seller health query error:', err.message);
      return res.status(500).json({ 
        error: 'Failed to fetch seller health metrics',
        details: err.message 
      });
    }
    
    // ====================================================================
    // NOT FOUND: Seller doesn't exist in database
    // ====================================================================
    if (!row || !row.seller_id) {
      return res.status(404).json({ 
        error: 'Seller not found',
        seller_id: sellerId
      });
    }

    // ====================================================================
    // SUCCESS: Return structured health metrics response
    // ====================================================================
    res.json({
      seller_id: row.seller_id,
      seller_name: row.seller_name,
      health_score: row.health_score,
      metrics: {
        credit_utilization_rate: row.credit_utilization_rate,
        payment_reliability_score: row.payment_reliability_score,
        lead_conversion_rate: row.lead_conversion_rate,
        wallet_health: {
          current_balance: row.current_balance,
          avg_weekly_change: row.avg_weekly_change,
          trend: row.trend
        }
      },
      risk_level: row.risk_level,
      last_updated: row.last_updated
    });
  });
});

module.exports = router;
