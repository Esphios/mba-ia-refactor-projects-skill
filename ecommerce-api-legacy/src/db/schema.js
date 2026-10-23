const { hashPassword } = require('../security/passwords');
const statements = [
  "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE, pass TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin')), active INTEGER NOT NULL DEFAULT 1, deleted_at TEXT, password_reset_required INTEGER NOT NULL DEFAULT 0)",
  'CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT NOT NULL, price REAL NOT NULL CHECK(price >= 0), active INTEGER NOT NULL DEFAULT 1)',
  'CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT, course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT)',
  'CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER NOT NULL UNIQUE REFERENCES enrollments(id) ON DELETE RESTRICT, amount REAL NOT NULL CHECK(amount >= 0), status TEXT NOT NULL)',
  'CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT NOT NULL, created_at DATETIME NOT NULL)',
  'CREATE INDEX IF NOT EXISTS enrollments_course ON enrollments(course_id)',
  'CREATE INDEX IF NOT EXISTS enrollments_user ON enrollments(user_id)',
  'CREATE INDEX IF NOT EXISTS payments_enrollment ON payments(enrollment_id)'
];
async function initializeSchema(db, config) {
  await db.transaction(async tx => {
    const existing = await tx.get("SELECT name FROM sqlite_master WHERE type='table' AND name='users'");
    if (existing) {
      const columns = await tx.all('PRAGMA table_info(users)');
      if (!['role', 'active', 'deleted_at', 'password_reset_required'].every(name => columns.some(column => column.name === name))) throw new Error('Legacy database requires explicit migration: npm run migrate:legacy');
    }
    for (const statement of statements) await tx.run(statement);
    // No automatic seed on an existing database, even if the flag is enabled.
    if (!existing && config.demoSeed) {
      await tx.run("INSERT INTO users(name,email,pass,role) VALUES(?,?,?,'admin')", ['Demo administrator', config.adminEmail.toLowerCase(), await hashPassword(config.adminPassword)]);
      await tx.run("INSERT INTO courses(title,price,active) VALUES('Clean Architecture',997,1),('Docker',497,1)");
    }
  });
}
module.exports = { initializeSchema };
