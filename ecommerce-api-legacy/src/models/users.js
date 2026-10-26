const users = {
    findByEmail: (tx, email) => tx.get('SELECT id,name,email,pass,active,role FROM users WHERE email=? LIMIT 1', [email]),
    async nextAvailableId(tx) {
        const row = await tx.get(`SELECT COALESCE(MAX(id),0)+1 AS id FROM (
            SELECT id FROM users UNION ALL SELECT user_id AS id FROM enrollments
        )`);
        return row.id;
    },
    async create(tx, name, email, passwordHash, role = 'user') {
        const id = await users.nextAvailableId(tx);
        await tx.run('INSERT INTO users(id,name,email,pass,role) VALUES (?,?,?,?,?)',
            [id,name,email,passwordHash,role]);
        return id;
    },
    async removeOrDeactivate(tx, id) {
        const linked = await tx.get('SELECT 1 AS found FROM enrollments WHERE user_id=? LIMIT 1', [id]);
        if (linked) await tx.run('UPDATE users SET active=0 WHERE id=?', [id]);
        else await tx.run('DELETE FROM users WHERE id=?', [id]);
    }
};
module.exports = users;
