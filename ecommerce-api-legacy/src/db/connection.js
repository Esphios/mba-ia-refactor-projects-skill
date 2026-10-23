const sqlite3 = require('sqlite3');
// Every connection operation enters the same queue. A transaction holds the queue
// until COMMIT/ROLLBACK; neither reads nor other writes can join it accidentally.
async function openDatabase(filename) {
  let connection;
  await new Promise((resolve, reject) => { connection = new sqlite3.Database(filename, error => error ? reject(error) : resolve()); });
  let tail = Promise.resolve();
  let queryCount = 0;
  let closed = false;
  function query(method, sql, params = []) {
    if (/^\s*(SELECT|WITH)\b/i.test(sql)) queryCount++;
    return new Promise((resolve, reject) => connection[method](sql, params, function(error, rows) {
      if (error) return reject(error);
      resolve(method === 'run' ? { lastID: this.lastID, changes: this.changes } : rows);
    }));
  }
  const session = { get: (sql, params) => query('get', sql, params), all: (sql, params) => query('all', sql, params), run: (sql, params) => query('run', sql, params) };
  function queued(operation) {
    if (closed) return Promise.reject(new Error('Database closed'));
    const result = tail.then(operation);
    tail = result.catch(() => {});
    return result;
  }
  await session.run('PRAGMA foreign_keys = ON');
  await session.run('PRAGMA busy_timeout = 5000');
  return {
    read: operation => queued(() => operation(session)),
    transaction: operation => queued(async () => {
      await session.run('BEGIN IMMEDIATE');
      try { const result = await operation(session); await session.run('COMMIT'); return result; }
      catch (error) { await session.run('ROLLBACK'); throw error; }
    }),
    get queryCount() { return queryCount; },
    resetQueryCount() { queryCount = 0; },
    async close() { closed = true; await tail; await new Promise((resolve, reject) => connection.close(error => error ? reject(error) : resolve())); }
  };
}
module.exports = { openDatabase };
