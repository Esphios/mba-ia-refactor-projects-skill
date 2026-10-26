const { PAID, DENIED } = require('../domain/paymentStatus');
const ACCEPTED_PREFIX = '4';
function simulatePayment(card) { return card.startsWith(ACCEPTED_PREFIX) ? PAID : DENIED; }
module.exports = { simulatePayment };
