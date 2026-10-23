const { authenticate, adminOnly, asyncHandler } = require('../middleware/authenticate');
function registerRoutes(app, controllers, auth) {
  app.post('/api/auth/login', asyncHandler(controllers.login));
  app.post('/api/checkout', authenticate(auth, true), asyncHandler(controllers.checkout));
  app.get('/api/admin/financial-report', authenticate(auth), adminOnly, asyncHandler(controllers.report));
  app.delete('/api/users/:id', authenticate(auth), asyncHandler(controllers.removeUser));
}
module.exports = { registerRoutes };
