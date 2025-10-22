// ============================================
//  File: part4_dashboard_optimized.js
// Description: Optimized Dashboard Endpoint
// ============================================

const express = require('express');
const router = express.Router();

// ✅ Optimized dashboard stats query (CTEs + joins)
router.get('/api/dashboard/stats', (req, res) => {
  const db = req.app.locals.db;

  const query = `
    WITH seller_data AS (
      SELECT s.market,
             COUNT(DISTINCT s.seller_id) AS total_sellers
      FROM sellers s
      GROUP BY s.market
    ),
    credit_data AS (
      SELECT s.market,
             SUM(CASE WHEN c.status = 'paid' THEN 1 ELSE 0 END) AS paid_credits,
             SUM(CASE WHEN c.status != 'cancelled' THEN 1 ELSE 0 END) AS total_credits
      FROM sellers s
      LEFT JOIN credits c ON s.seller_id = c.seller_id
      GROUP BY s.market
    ),
    wallet_data AS (
      SELECT s.market,
             ROUND(AVG(w.amount), 2) AS avg_wallet_change
      FROM sellers s
      LEFT JOIN wallet_transactions w ON s.seller_id = w.seller_id
      GROUP BY s.market
    )
    SELECT sd.market,
           sd.total_sellers,
           cd.paid_credits,
           cd.total_credits,
           wd.avg_wallet_change,
           ROUND(cd.paid_credits * 1.0 / cd.total_credits, 2) AS payment_success_rate
    FROM seller_data sd
    JOIN credit_data cd ON sd.market = cd.market
    JOIN wallet_data wd ON sd.market = wd.market;
  `;

  db.all(query, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

module.exports = router;
