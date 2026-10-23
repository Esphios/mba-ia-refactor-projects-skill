const users = require('../models/userModel');
const { verifyPassword } = require('../security/passwords');
const { issueToken, verifyToken } = require('../security/tokens');
const { HttpError } = require('../errors');
function authService(db, config, dummyHash) {
  return {
    async login(email, password) {
      const user = await db.read(tx => users.byEmail(tx, email));
      const valid = await verifyPassword(password, user?.pass || dummyHash);
      if (!valid || !user?.active || user.password_reset_required) throw new HttpError(401, 'Não autenticado');
      return { access_token: issueToken(user.id, config.authSecret, config.tokenTtlSeconds), token_type: 'Bearer', expires_in: config.tokenTtlSeconds };
    },
    async authenticate(token) {
      const id = verifyToken(token, config.authSecret);
      const user = await db.read(tx => users.byId(tx, id));
      if (!user?.active || user.password_reset_required) throw new HttpError(401, 'Não autenticado');
      return { id: user.id, role: user.role };
    }
  };
}
module.exports = { authService };
