const users = require('../models/userModel');
const records = require('../models/checkoutModels');
const { hashPassword, verifyPassword } = require('../security/passwords');
const gateway = require('./simulatedPaymentGateway');
const { HttpError } = require('../errors');
function checkoutService(db, logger) {
  return async (input, actor) => {
    const result = await db.transaction(async tx => {
      const course = await records.activeCourse(tx, input.courseId);
      if (!course) throw new HttpError(404, 'Curso não encontrado');
      let user = await users.byEmail(tx, input.email);
      if (user) {
        const matches = actor ? actor.id === user.id : await verifyPassword(input.password, user.pass);
        if (!user.active || user.password_reset_required || !matches) throw new HttpError(401, 'Não autenticado');
      } else if (typeof input.password !== 'string' || input.password.length < 8) throw new HttpError(400, 'Bad Request');
      if (!gateway.approve(input.card)) throw new HttpError(400, 'Pagamento recusado');
      if (!user) {
        const created = await users.create(tx, input.name, input.email, await hashPassword(input.password));
        user = { id: created.lastID };
      }
      const enrollment = await records.enroll(tx, user.id, input.courseId);
      await records.pay(tx, enrollment.lastID, course.price);
      await records.audit(tx, input.courseId, user.id);
      return { msg: 'Sucesso', enrollment_id: enrollment.lastID };
    });
    // Logging cannot make a committed operation appear to fail.
    try { logger({ event: 'checkout', outcome: 'PAID', enrollment_id: result.enrollment_id }); } catch {}
    return result;
  };
}
module.exports = { checkoutService };
