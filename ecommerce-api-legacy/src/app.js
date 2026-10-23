const express = require('express');
const { loadConfig } = require('./config');
const { openDatabase } = require('./db/connection');
const { initializeSchema } = require('./db/schema');
const { hashPassword } = require('./security/passwords');
const { authService } = require('./services/authService');
const { checkoutService } = require('./services/checkoutService');
const { userLifecycleService } = require('./services/userLifecycleService');
const { registerRoutes } = require('./routes');
const { errorHandler } = require('./errors');
async function createApplication({ config = loadConfig(), logger = event => console.log(JSON.stringify(event)) } = {}) {
  const db = await openDatabase(config.databasePath);
  try {
    await initializeSchema(db, config);
    const auth = authService(db, config, await hashPassword(require('node:crypto').randomBytes(32).toString('hex')));
    const app = express();
    app.disable('x-powered-by');
    app.use(express.json({ limit: '16kb' }));
    registerRoutes(app, {
      login: require('./controllers/authController')(auth),
      checkout: require('./controllers/checkoutController')(checkoutService(db, logger)),
      report: require('./controllers/reportController')(db),
      removeUser: require('./controllers/userController')(userLifecycleService(db))
    }, auth);
    app.use(errorHandler);
    return { app, db, close: () => db.close() };
  } catch (error) { await db.close(); throw error; }
}
module.exports = { createApplication };
