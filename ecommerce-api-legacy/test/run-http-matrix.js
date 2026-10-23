const assert = require('node:assert/strict');
const { fork, spawn } = require('node:child_process');
const { once } = require('node:events');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const sqlite3 = require('sqlite3');
const { hashPassword } = require('../src/security/passwords');

async function main() {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'project2-http-'));
  const database = path.join(directory, 'fixture.db');
  const env = { ...process.env, AUTH_SECRET: 'disposable-http-runner-secret-at-least-32-bytes', DEMO_SEED: 'true', DEMO_ADMIN_EMAIL: 'http-admin@example.test', DEMO_ADMIN_PASSWORD: 'http-admin-fixture-password', DB_PATH: database, PORT: '0', TOKEN_TTL_SECONDS: '60' };
  const child = fork(path.resolve(__dirname, '../src/server.js'), [], { env, silent: true });
  let output = '';
  child.stdout.on('data', chunk => { output += chunk; process.stdout.write(chunk); });
  child.stderr.on('data', chunk => { output += chunk; process.stderr.write(chunk); });
  let connection;
  let timer;
  let success = false;
  try {
    const ready = await Promise.race([
      once(child, 'message').then(([message]) => message),
      once(child, 'exit').then(([code]) => { throw new Error(`server exited before readiness: ${code}`); }),
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('startup timeout')), 15000); })
    ]);
    clearTimeout(timer);
    assert.equal(ready.event, 'ready');
    connection = new sqlite3.Database(database);
    const run = (sql, params = []) => new Promise((resolve, reject) => connection.run(sql, params, function (error) { error ? reject(error) : resolve({ lastID: this.lastID, changes: this.changes }); }));
    const get = (sql, params = []) => new Promise((resolve, reject) => connection.get(sql, params, (error, row) => error ? reject(error) : resolve(row)));
    const call = async (name, endpoint, method, body, token, expected) => {
      const response = await fetch(`http://127.0.0.1:${ready.port}${endpoint}`, { method, headers: { 'content-type': 'application/json', ...(token ? { authorization: `Bearer ${token}` } : {}) }, body: body === undefined ? undefined : JSON.stringify(body) });
      const text = await response.text();
      let data; try { data = JSON.parse(text); } catch { data = text; }
      assert.equal(response.status, expected, `${name}: ${text}`);
      console.log(JSON.stringify({ case: name, method, path: endpoint, expected, observed: response.status, passed: true }));
      return data;
    };
    const input = { usr: 'HTTP Student', eml: 'http-student@example.test', pwd: 'http-student-password', c_id: 1, card: '4111111111111111' };
    console.log(JSON.stringify({ node: process.version, express: require('express/package.json').version, sqlite3: require('sqlite3/package.json').version, sqlite: (await get('SELECT sqlite_version() version')).version, database: 'disposable temporary file', listening_after_schema: true }));
    await call('anonymous report', '/api/admin/financial-report', 'GET', undefined, undefined, 401);
    await call('anonymous deletion', '/api/users/1', 'DELETE', undefined, undefined, 401);
    await call('login bad input', '/api/auth/login', 'POST', {}, undefined, 400);
    await call('login invalid credentials', '/api/auth/login', 'POST', { email: env.DEMO_ADMIN_EMAIL, password: 'wrong' }, undefined, 401);
    const admin = (await call('administrator login', '/api/auth/login', 'POST', { email: env.DEMO_ADMIN_EMAIL, password: env.DEMO_ADMIN_PASSWORD }, undefined, 200)).access_token;
    await call('checkout missing input', '/api/checkout', 'POST', {}, undefined, 400);
    await call('checkout invalid card type', '/api/checkout', 'POST', { ...input, card: 42 }, undefined, 400);
    await call('checkout missing new-account password', '/api/checkout', 'POST', { ...input, pwd: undefined }, undefined, 400);
    await call('checkout absent course', '/api/checkout', 'POST', { ...input, c_id: 99999 }, undefined, 404);
    await call('checkout denied', '/api/checkout', 'POST', { ...input, card: '5111111111111111' }, undefined, 400);
    assert.equal((await get('SELECT COUNT(*) count FROM enrollments')).count, 0);
    assert.equal((await get('SELECT COUNT(*) count FROM users')).count, 1);
    const paid = await call('checkout approved shape', '/api/checkout', 'POST', input, undefined, 200);
    assert.deepEqual(paid, { msg: 'Sucesso', enrollment_id: 1 });
    const user = await get('SELECT id FROM users WHERE email=?', [input.eml]);
    const token = (await call('student login', '/api/auth/login', 'POST', { email: input.eml, password: input.pwd }, undefined, 200)).access_token;
    await call('student report denied', '/api/admin/financial-report', 'GET', undefined, token, 403);
    await call('student cannot delete administrator', '/api/users/1', 'DELETE', undefined, token, 403);
    await call('checkout existing identity missing', '/api/checkout', 'POST', { ...input, pwd: undefined }, undefined, 401);
    await call('checkout existing wrong password', '/api/checkout', 'POST', { ...input, pwd: 'incorrect' }, undefined, 401);
    await call('checkout existing bearer identity', '/api/checkout', 'POST', { ...input, pwd: undefined }, token, 200);
    await call('tampered credential', '/api/admin/financial-report', 'GET', undefined, admin + 'x', 401);
    const { issueToken } = require('../src/security/tokens');
    const expired = issueToken(1, env.AUTH_SECRET, 60, Math.floor(Date.now() / 1000) - 120);
    await call('expired credential', '/api/admin/financial-report', 'GET', undefined, expired, 401);
    const report = await call('administrator report authorized', '/api/admin/financial-report', 'GET', undefined, admin, 200);
    assert.deepEqual(report, [{ course: 'Clean Architecture', revenue: 1994, students: [{ student: 'HTTP Student', paid: 997 }, { student: 'HTTP Student', paid: 997 }] }, { course: 'Docker', revenue: 0, students: [] }]);
    await call('delete invalid ID', '/api/users/bad', 'DELETE', undefined, admin, 400);
    await call('delete absent user', '/api/users/9999', 'DELETE', undefined, admin, 404);
    const before = await get('SELECT (SELECT COUNT(*) FROM users) users,(SELECT COUNT(*) FROM enrollments) enrollments,(SELECT COUNT(*) FROM payments) payments,(SELECT COUNT(*) FROM audit_logs) audit');
    await run("CREATE TRIGGER fixture_failure BEFORE INSERT ON payments BEGIN SELECT RAISE(ABORT,'induced failure'); END");
    await call('induced payment failure rollback', '/api/checkout', 'POST', { ...input, eml: 'rollback@example.test' }, undefined, 500);
    assert.deepEqual(await get('SELECT (SELECT COUNT(*) FROM users) users,(SELECT COUNT(*) FROM enrollments) enrollments,(SELECT COUNT(*) FROM payments) payments,(SELECT COUNT(*) FROM audit_logs) audit'), before);
    await run('DROP TRIGGER fixture_failure');
    await Promise.all(Array.from({ length: 5 }, (_, index) => call(`concurrent ${index}`, '/api/checkout', 'POST', { ...input, eml: `parallel-${index}@example.test` }, undefined, 200)));
    assert.equal((await get('SELECT COUNT(*) count FROM payments')).count, before.payments + 5);
    await call('self deactivation preserves financial history', `/api/users/${user.id}`, 'DELETE', undefined, token, 200);
    assert.equal((await get('SELECT active FROM users WHERE id=?', [user.id])).active, 0);
    assert.equal((await get('SELECT COUNT(*) count FROM enrollments WHERE user_id=?', [user.id])).count, 2);
    await call('deactivated identity denied', '/api/checkout', 'POST', input, token, 401);
    const unreferenced = await run("INSERT INTO users(name,email,pass,role,active) VALUES(?,?,?,'user',1)", ['Delete fixture', 'delete@example.test', await hashPassword('deletion-password')]);
    await call('administrator physical deletion without relationships', `/api/users/${unreferenced.lastID}`, 'DELETE', undefined, admin, 200);
    assert.equal(await get('SELECT id FROM users WHERE id=?', [unreferenced.lastID]), undefined);
    await run("CREATE TRIGGER fixture_delete_failure BEFORE DELETE ON users BEGIN SELECT RAISE(ABORT,'induced deletion failure'); END");
    await call('delete database failure', '/api/users/1', 'DELETE', undefined, admin, 500);
    await run('DROP TRIGGER fixture_delete_failure');
    await run('ALTER TABLE courses RENAME TO unavailable_courses');
    await call('report database failure', '/api/admin/financial-report', 'GET', undefined, admin, 500);
    await call('checkout database failure', '/api/checkout', 'POST', input, token, 401); // current identity remains deactivated
    await call('checkout database lookup failure', '/api/checkout', 'POST', { ...input, eml: 'db-error@example.test' }, undefined, 500);
    assert.doesNotMatch(output, /4111111111111111|http-student-password|disposable-http-runner-secret/);
    console.log('HTTP_MATRIX_PASS: all 3 original endpoints and new login; success/denial/errors/rollback/concurrency verified against a real child process');
    success = true;
  } finally {
    clearTimeout(timer);
    if (connection) await new Promise(resolve => connection.close(resolve));
    if (child.connected) child.send('shutdown');
    if (child.exitCode === null) {
      let stopTimer;
      await Promise.race([once(child, 'exit'), new Promise(resolve => { stopTimer = setTimeout(() => { child.kill(); resolve(); }, 5000); })]);
      clearTimeout(stopTimer);
    }
    assert.equal(path.dirname(path.resolve(directory)), path.resolve(os.tmpdir()));
    await fs.rm(directory, { recursive: true });
  }
  if (!success) throw new Error('HTTP validation incomplete');
  // A real invalid-config process must exit without exposing any secret.
  const invalid = spawn(process.execPath, [path.resolve(__dirname, '../src/server.js')], { env: { ...process.env, AUTH_SECRET: '' } });
  let invalidOutput = ''; invalid.stderr.on('data', chunk => { invalidOutput += chunk; });
  const [code] = await once(invalid, 'exit'); assert.equal(code, 1); assert.match(invalidOutput, /AUTH_SECRET/);
  console.log('STARTUP_FAILURE_PASS: missing required signing secret exits 1 without listening');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
