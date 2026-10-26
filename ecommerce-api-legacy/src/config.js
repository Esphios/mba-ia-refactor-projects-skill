function loadConfig(env = process.env) {
    const port = Number(env.PORT ?? 3000);
    if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT inválida');
    return { port, host: env.HOST || '127.0.0.1', databasePath: env.LMS_DB || ':memory:', demo: env.LMS_DEMO === '1' };
}
module.exports = { loadConfig };
