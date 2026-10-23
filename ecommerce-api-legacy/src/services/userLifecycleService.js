const users = require('../models/userModel');
const { HttpError } = require('../errors');
function userLifecycleService(db) {
  return (id, actor) => db.transaction(async tx => {
    // Re-read actor under the transaction lock so deactivation/role changes cannot race.
    const currentActor = await users.byId(tx, actor.id);
    if (!currentActor?.active || currentActor.password_reset_required) throw new HttpError(401, 'Não autenticado');
    if (currentActor.id !== id && currentActor.role !== 'admin') throw new HttpError(403, 'Não autorizado');
    if (!await users.byId(tx, id)) throw new HttpError(404, 'Usuário não encontrado');
    if (await users.hasRelationships(tx, id)) {
      await users.deactivate(tx, id);
      return { msg: 'Usuário desativado; histórico financeiro preservado', id, action: 'deactivated' };
    }
    const result = await users.remove(tx, id);
    if (!result.changes) throw new HttpError(404, 'Usuário não encontrado');
    return { msg: 'Usuário deletado', id, action: 'deleted' };
  });
}
module.exports = { userLifecycleService };
