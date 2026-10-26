const { randomBytes, scrypt, timingSafeEqual } = require('node:crypto');
const { promisify } = require('node:util');
const derive = promisify(scrypt);
const OPTIONS = { N: 16384, r: 8, p: 1, maxmem: 64 * 1024 * 1024 };
function validPassword(password) { return typeof password === 'string' && password.length > 0 && Buffer.byteLength(password, 'utf8') <= 1024; }
async function hashPassword(password) {
    if (!validPassword(password)) throw new Error('Senha inválida');
    const salt = randomBytes(16).toString('hex');
    const key = await derive(password, salt, 64, OPTIONS);
    return `scrypt$${salt}$${key.toString('hex')}`;
}
async function verifyPassword(stored, password) {
    if (!validPassword(password) || typeof stored !== 'string') return false;
    const match = /^scrypt\$([a-f0-9]{32})\$([a-f0-9]{128})$/.exec(stored);
    if (!match) return false;
    const candidate = await derive(password, match[1], 64, OPTIONS);
    return timingSafeEqual(candidate, Buffer.from(match[2], 'hex'));
}
module.exports = { hashPassword, verifyPassword, validPassword };
