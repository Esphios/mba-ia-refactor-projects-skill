const { createHmac, timingSafeEqual } = require('node:crypto');
const { HttpError } = require('../errors');
const signature = (payload, secret) => createHmac('sha256', secret).update(payload).digest('base64url');
function issueToken(userId, secret, ttlSeconds, now = Math.floor(Date.now() / 1000)) {
  const payload = Buffer.from(JSON.stringify({ sub: userId, iat: now, exp: now + ttlSeconds, aud: 'ecommerce-api' })).toString('base64url');
  return `${payload}.${signature(payload, secret)}`;
}
function verifyToken(token, secret, now = Math.floor(Date.now() / 1000)) {
  try {
    if (typeof token !== 'string' || token.length > 2048) throw new Error();
    const parts = token.split('.');
    if (parts.length !== 2 || !/^[A-Za-z0-9_-]+$/.test(parts[0]) || !/^[A-Za-z0-9_-]{43}$/.test(parts[1])) throw new Error();
    const expected = Buffer.from(signature(parts[0], secret));
    const actual = Buffer.from(parts[1]);
    if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) throw new Error();
    const claims = JSON.parse(Buffer.from(parts[0], 'base64url').toString());
    if (!Number.isSafeInteger(claims.sub) || claims.sub < 1 || !Number.isSafeInteger(claims.exp) || !Number.isSafeInteger(claims.iat) || claims.iat > now || claims.exp <= now || claims.exp <= claims.iat || claims.aud !== 'ecommerce-api') throw new Error();
    return claims.sub;
  } catch { throw new HttpError(401, 'Não autenticado'); }
}
module.exports = { issueToken, verifyToken };
