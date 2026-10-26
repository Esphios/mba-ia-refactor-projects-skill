class HttpError extends Error {
    constructor(status, message) { super(message); this.status = status; }
}
function errorHandler(error, req, res, next) {
    if (res.headersSent) return next(error);
    const status = error instanceof HttpError ? error.status : error.type === 'entity.parse.failed' ? 400 : error.status === 413 ? 413 : 500;
    if (status === 401) res.set('WWW-Authenticate', 'Basic realm="LMS", charset="UTF-8"');
    res.status(status).send(error instanceof HttpError ? error.message : status === 500 ? 'Erro DB' : 'Bad Request');
}
module.exports = { HttpError, errorHandler };
