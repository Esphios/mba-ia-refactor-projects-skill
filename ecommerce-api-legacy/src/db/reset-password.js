const { openDatabase } = require('./connection');
const { hashPassword } = require('../security/passwords');
async function resetPassword(db, email, password) {
  if (typeof email !== 'string' || typeof password !== 'string' || password.length < 8 || password.length > 256) throw new Error('RESET_EMAIL and RESET_PASSWORD (8..256 characters) are required');
  const hash = await hashPassword(password);
  await db.transaction(async tx => {
    const result = await tx.run('UPDATE users SET pass=?,password_reset_required=0 WHERE email=? COLLATE NOCASE', [hash, email]);
    if (result.changes !== 1) throw new Error('Expected exactly one account');
  });
}
async function main() {
  if (!process.env.DB_PATH || process.env.DB_PATH === ':memory:') throw new Error('DB_PATH must name an existing database file');
  await require('node:fs/promises').access(process.env.DB_PATH);
  const db = await openDatabase(process.env.DB_PATH);
  try { await resetPassword(db, process.env.RESET_EMAIL, process.env.RESET_PASSWORD); console.log(JSON.stringify({ event: 'credential_reset_complete' })); }
  finally { await db.close(); }
}
if (require.main === module) main().catch(() => { console.error('Credential reset failed; verify account and configuration'); process.exitCode = 1; });
module.exports = { resetPassword };
