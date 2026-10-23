const { HttpError } = require('../errors');
const validEmail = value => typeof value === 'string' && value.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
function checkoutInput(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body) || typeof body.usr !== 'string' || !body.usr.trim() || body.usr.length > 120 || !validEmail(body.eml) || !Number.isSafeInteger(body.c_id) || body.c_id <= 0 || typeof body.card !== 'string' || !/^\d{12,19}$/.test(body.card) || (body.pwd !== undefined && (typeof body.pwd !== 'string' || !body.pwd || body.pwd.length > 256))) throw new HttpError(400, 'Bad Request');
  return { name: body.usr.trim(), email: body.eml.toLowerCase(), password: body.pwd, courseId: body.c_id, card: body.card };
}
function loginInput(body) {
  if (!body || !validEmail(body.email) || typeof body.password !== 'string' || !body.password || body.password.length > 256) throw new HttpError(400, 'Bad Request');
  return { email: body.email.toLowerCase(), password: body.password };
}
function userIdInput(value) {
  if (!/^[1-9]\d*$/.test(value) || !Number.isSafeInteger(Number(value))) throw new HttpError(400, 'Bad Request');
  return Number(value);
}
module.exports = { checkoutInput, loginInput, userIdInput };
