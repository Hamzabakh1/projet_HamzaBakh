// server.js
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = 3000;

const dbPath = path.join(__dirname, '../exam_database.db');
const db = new sqlite3.Database(dbPath);
app.locals.db = db;

app.use(express.json());


const dashboardRoutes = require('./part4_dashboard_optimized');
const sellerHealthRoutes = require('./part4_seller_health');

app.use(dashboardRoutes);
app.use(sellerHealthRoutes);

app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});
