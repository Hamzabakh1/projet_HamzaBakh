// ============================================
//  File: part4_seller_health.js
// Description: Seller Health Analytics Endpoint
// ============================================

const express = require('express');
const router = express.Router();

//  GET /api/analytics/seller-health/:seller_id
// Returns seller health metrics and risk classification
router.get('/api/analytics/seller-health/:seller_id', (req, res) => {
  const db = req.app.locals.db;
  const sellerId = parseInt(req.params.seller_id);

  // Input validation
  if (isNaN(sellerId)) {
    return res.status(400).json({ error: 'seller_id must be an integer' });
  }

  const query = `
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
    lead_stats AS (
      SELECT
        seller_id,
        SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) * 1.0 / 
          NULLIF(COUNT(lead_id), 0) AS lead_conversion
      FROM leads
      WHERE seller_id = ?
      GROUP BY seller_id
    ),
    wallet_stats AS (
      SELECT
        seller_id,
        SUM(amount) AS current_balance,
        AVG(amount) AS avg_weekly_change
      FROM wallet_transactions
      WHERE seller_id = ?
      GROUP BY seller_id
    )
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

  db.get(query, [sellerId, sellerId, sellerId, sellerId], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!row || !row.seller_id) return res.status(404).json({ error: 'Seller not found' });

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
