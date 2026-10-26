const { basicCredentials } = require('../security/identity');
const wrap = handler => (req,res,next) => Promise.resolve().then(() => handler(req,res)).catch(next);
function registerRoutes(app, controllers) {
    app.post('/api/checkout',wrap(async (req,res) => res.status(200).json(await controllers.checkout(req.body))));
    app.get('/api/admin/financial-report',wrap(async (req,res) => res.json(await controllers.report(basicCredentials(req.get('Authorization'))))));
    app.delete('/api/users/:id',wrap(async (req,res) => res.send(await controllers.remove(req.params.id,basicCredentials(req.get('Authorization'))))));
}
module.exports = { registerRoutes };
