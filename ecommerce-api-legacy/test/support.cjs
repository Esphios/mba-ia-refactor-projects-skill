const { once } = require('node:events');

async function fixture() {
  const { createApplication } = require('../src/app');
  const { app, database, close } = await createApplication({ databasePath: ':memory:', demo: true });
  const server = app.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const base = `http://127.0.0.1:${server.address().port}`;
  const request = async (url, { auth, body, method = 'GET', headers = {} } = {}) => {
    const response = await fetch(base + url, { method, headers: {
      ...(body === undefined ? {} : {'Content-Type':'application/json'}),
      ...(auth ? {Authorization:'Basic '+Buffer.from(auth).toString('base64')} : {}), ...headers
    }, body: body === undefined ? undefined : JSON.stringify(body) });
    const text = await response.text();
    return { status:response.status, text, json:() => JSON.parse(text), headers: response.headers };
  };
  return { database, request, async close() { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); await close(); } };
}
const checkout = (extra = {}) => ({usr:'Áluna',eml:'aluna@example.test',pwd:'senha-💜-completa',c_id:2,card:'4111222233334444',...extra});
module.exports = {fixture, checkout};
