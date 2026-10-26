const users = require('../models/users');
const { authenticate } = require('../security/identity');
const { HttpError } = require('../http/errors');
function deletionService(database) {
    return (id,credentials) => database.transaction(async tx => {
        const identity = await authenticate(tx,credentials.email,credentials.password);
        if (identity.id !== id && identity.role !== 'admin') throw new HttpError(403,'Não autorizado');
        await users.removeOrDeactivate(tx,id);
    });
}
module.exports = { deletionService };
