const { checkoutInput } = require('../validation/inputs');
module.exports = checkout => async (req, res) => { res.json(await checkout(checkoutInput(req.body), req.actor)); };
