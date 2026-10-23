const { financialReport } = require('../models/financialReportModel');
module.exports = db => async (req, res) => {
  res.json(await db.read(async tx => {
    // Middleware already verifies current state; keep report retrieval in a single
    // queued read operation so checkout commits cannot interleave its query.
    return financialReport(tx);
  }));
};
