const { authenticate } = require('../security/identity');
const { financialReport } = require('../models/financialReport');
const { HttpError } = require('../http/errors');
function reportController(database) {
    return credentials => database.read(async tx => {
        const identity = await authenticate(tx,credentials.email,credentials.password);
        if (identity.role !== 'admin') throw new HttpError(403,'Não autorizado');
        return financialReport(tx);
    });
}
module.exports = { reportController };
