// Teaching-only simulation retained from the original contract; no real charge.
const APPROVED_CARD_PREFIX = '4';
module.exports = { approve: card => card.startsWith(APPROVED_CARD_PREFIX) };
