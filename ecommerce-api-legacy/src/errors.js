class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
function errorHandler(error, req, res, next) {
  if (res.headersSent) return next(error);
  if (error instanceof HttpError) return res.status(error.status).send(error.message);
  if (error.type === 'entity.parse.failed' || error.type === 'entity.too.large') return res.status(400).send('Bad Request');
  return res.status(500).send('Erro DB');
}
module.exports = { HttpError, errorHandler };
