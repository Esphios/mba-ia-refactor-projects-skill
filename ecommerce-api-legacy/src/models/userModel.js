module.exports = {
  byId: (tx, id) => tx.get('SELECT * FROM users WHERE id=?', [id]),
  byEmail: (tx, email) => tx.get('SELECT * FROM users WHERE email=? COLLATE NOCASE', [email]),
  create: (tx, name, email, pass) => tx.run("INSERT INTO users(name,email,pass,role,active) VALUES(?,?,?,'user',1)", [name, email, pass]),
  hasRelationships: async (tx, id) => Boolean(await tx.get('SELECT 1 FROM enrollments WHERE user_id=? LIMIT 1', [id])),
  deactivate: (tx, id) => tx.run("UPDATE users SET active=0, deleted_at=datetime('now') WHERE id=?", [id]),
  remove: (tx, id) => tx.run('DELETE FROM users WHERE id=?', [id])
};
