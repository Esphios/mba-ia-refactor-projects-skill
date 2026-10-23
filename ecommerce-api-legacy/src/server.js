const { createApplication } = require('./app');
const { loadConfig } = require('./config');
async function start() {
  const config = loadConfig();
  const instance = await createApplication({ config });
  const server = instance.app.listen(config.port, '127.0.0.1');
  try { await new Promise((resolve, reject) => { server.once('listening', resolve); server.once('error', reject); }); }
  catch (error) { await instance.close(); throw error; }
  console.log(JSON.stringify({ event: 'ready', port: server.address().port, database: config.databasePath === ':memory:' ? 'memory' : 'file' }));
  let stopping = false;
  async function stop() {
    if (stopping) return;
    stopping = true;
    await new Promise(resolve => server.close(resolve));
    await instance.close();
    console.log(JSON.stringify({ event: 'stopped' }));
  }
  process.once('SIGINT', stop);
  process.once('SIGTERM', stop);
  if (process.send) { process.send({ event: 'ready', port: server.address().port }); process.on('message', message => { if (message === 'shutdown') stop().then(() => process.disconnect()); }); }
  return { server, stop };
}
if (require.main === module) start().catch(error => { console.error(JSON.stringify({ event: 'startup_failed', message: /AUTH_SECRET|PORT|TOKEN_TTL|DEMO_ADMIN|Legacy database/.test(error.message) ? error.message : 'Database initialization failed' })); process.exitCode = 1; });
module.exports = { start };
