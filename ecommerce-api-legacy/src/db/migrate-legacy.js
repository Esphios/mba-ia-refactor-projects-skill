const { openDatabase } = require('./connection');
// Explicit, additive and idempotent. A backup is required by the CLI. Do not infer
// plaintext vs the old lossy ten-character transform: require credential reset.
async function migrateLegacy(db) {
  await db.transaction(async tx => {
    const columns = await tx.all('PRAGMA table_info(users)');
    if (!columns.length) throw new Error('No legacy users table found');
    const additions = {
      role: "TEXT NOT NULL DEFAULT 'user'",
      active: 'INTEGER NOT NULL DEFAULT 1',
      deleted_at: 'TEXT',
      password_reset_required: 'INTEGER NOT NULL DEFAULT 1'
    };
    for (const [name, definition] of Object.entries(additions)) {
      if (!columns.some(column => column.name === name)) await tx.run(`ALTER TABLE users ADD COLUMN ${name} ${definition}`);
    }
    // Fail and roll back rather than merge/delete duplicate historical accounts.
    await tx.run('CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique ON users(email COLLATE NOCASE)');
    await tx.run('CREATE INDEX IF NOT EXISTS enrollments_user ON enrollments(user_id)');
    await tx.run('CREATE INDEX IF NOT EXISTS payments_enrollment ON payments(enrollment_id)');
  });
}
async function main() {
  const fs = require('node:fs/promises');
  const path = require('node:path');
  const filename = process.env.DB_PATH;
  if (!filename || filename === ':memory:') throw new Error('DB_PATH must name an existing database file');
  // Stop the server before running. copyFile EXCL prevents accidental backup overwrite.
  await fs.copyFile(filename, filename + '.pre-migration.bak', require('node:fs').constants.COPYFILE_EXCL);
  const db = await openDatabase(filename);
  try { await migrateLegacy(db); console.log(JSON.stringify({ event: 'migration_complete', backup: path.basename(filename) + '.pre-migration.bak', credential_reset_required: true })); }
  finally { await db.close(); }
}
if (require.main === module) main().catch(() => { console.error('Migration failed; keep the backup and inspect duplicate accounts/schema before retrying'); process.exitCode = 1; });
module.exports = { migrateLegacy };
