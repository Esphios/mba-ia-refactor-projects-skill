const { loginInput } = require('../validation/inputs');
module.exports = auth => async (req, res) => { const input = loginInput(req.body); res.json(await auth.login(input.email, input.password)); };
