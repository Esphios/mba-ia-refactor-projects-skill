const users = require('../models/users');
const { verifyPassword } = require('./passwords');
const { HttpError } = require('../http/errors');
async function authenticate(tx, email, password) {
    const user = await users.findByEmail(tx, email);
    if (!user || !await verifyPassword(user.pass, password)) throw new HttpError(401, 'Não autenticado');
    if (user.active !== 1) throw new HttpError(403, 'Conta inativa');
    return user;
}
function basicCredentials(header) {
    if (typeof header !== 'string' || !/^Basic [A-Za-z0-9+/]+={0,2}$/i.test(header)) throw new HttpError(401, 'Não autenticado');
    const bytes = Buffer.from(header.slice(6), 'base64');
    const decoded = bytes.toString('utf8');
    const colon = decoded.indexOf(':');
    if (colon <= 0 || !bytes.equals(Buffer.from(decoded,'utf8'))) throw new HttpError(401, 'Não autenticado');
    return {email: decoded.slice(0, colon), password: decoded.slice(colon+1)};
}
module.exports = { authenticate, basicCredentials };
