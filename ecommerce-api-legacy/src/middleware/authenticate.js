const { HttpError } = require('../errors');
const asyncHandler = handler => (req, res, next) => Promise.resolve().then(() => handler(req, res, next)).catch(next);
function authenticate(auth, optional = false) {
  return asyncHandler(async (req, res, next) => {
    const header = req.get('authorization');
    if (!header && optional) return next();
    if (!header || !/^Bearer \S+$/.test(header)) throw new HttpError(401, 'Não autenticado');
    req.actor = await auth.authenticate(header.slice(7));
    next();
  });
}
function adminOnly(req, res, next) {
  if (req.actor?.role !== 'admin') return next(new HttpError(403, 'Não autorizado'));
  next();
}
module.exports = { authenticate, adminOnly, asyncHandler };
