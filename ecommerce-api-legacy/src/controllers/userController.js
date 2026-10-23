const { userIdInput } = require('../validation/inputs');
module.exports = lifecycle => async (req, res) => { res.json(await lifecycle(userIdInput(req.params.id), req.actor)); };
