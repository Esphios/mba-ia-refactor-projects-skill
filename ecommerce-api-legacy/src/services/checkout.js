const users = require('../models/users');
const learning = require('../models/learning');
const { hashPassword, verifyPassword } = require('../security/passwords');
const { simulatePayment } = require('./paymentSimulator');
const { DENIED } = require('../domain/paymentStatus');
const { HttpError } = require('../http/errors');
async function persist(operation,message) {
    try { return await operation(); }
    catch { throw new HttpError(500,message); }
}
function checkoutService(database) {
    return input => database.transaction(async tx => {
        const course = await learning.course(tx, input.courseId);
        if (!course) throw new HttpError(404, 'Curso não encontrado');
        const existing = await users.findByEmail(tx, input.email);
        if (existing) {
            if (!await verifyPassword(existing.pass,input.password)) throw new HttpError(401, 'Não autenticado');
            if (existing.active !== 1) throw new HttpError(403, 'Conta inativa');
        }
        const status = simulatePayment(input.card);
        if (status === DENIED) throw new HttpError(400, 'Pagamento recusado');
        const userId = existing ? existing.id : await persist(async()=>users.create(tx,input.name,input.email,await hashPassword(input.password)),'Erro ao criar usuário');
        const enrollmentId = await persist(()=>learning.enroll(tx,userId,input.courseId),'Erro Matrícula');
        await persist(()=>learning.payment(tx,enrollmentId,course.price,status),'Erro Pagamento');
        await learning.audit(tx,`Checkout curso ${input.courseId} por ${userId}`);
        return enrollmentId;
    });
}
module.exports = { checkoutService };
