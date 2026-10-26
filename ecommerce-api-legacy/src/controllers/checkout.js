const { validPassword } = require('../security/passwords');
const { HttpError } = require('../http/errors');
function checkoutController(checkout) {
    return async body => {
        if (!body || typeof body !== 'object' || Array.isArray(body)) throw new HttpError(400,'Bad Request');
        const { usr:name, eml:email, pwd:password, c_id:courseId, card } = body;
        if (typeof name !== 'string' || !name.trim() || typeof email !== 'string' || !email.trim() ||
            !validPassword(password) || !Number.isSafeInteger(courseId) || courseId <= 0 || typeof card !== 'string' || !card)
            throw new HttpError(400,'Bad Request');
        return {msg:'Sucesso',enrollment_id:await checkout({name,email,password,courseId,card})};
    };
}
module.exports = { checkoutController };
