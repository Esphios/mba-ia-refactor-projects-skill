const { HttpError } = require('../http/errors');
function deletionController(remove) {
    return async (rawId,credentials) => {
        const id = Number(rawId);
        if (!/^[1-9][0-9]*$/.test(rawId) || !Number.isSafeInteger(id)) throw new HttpError(400,'Bad Request');
        await remove(id,credentials);
        return 'Usuário removido.';
    };
}
module.exports = { deletionController };
