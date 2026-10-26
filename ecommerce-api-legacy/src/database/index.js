const sqlite3 = require('sqlite3');

async function openDatabase(filename = ':memory:') {
    const connection = await new Promise((resolve, reject) => {
        const db = new sqlite3.Database(filename, error => error ? reject(error) : resolve(db));
    });
    let tail = Promise.resolve();
    let closing = false;
    const raw = Object.fromEntries(['run', 'get', 'all'].map(method => [method,
        (sql, params = []) => new Promise((resolve, reject) => {
            connection[method](sql, params, function(error, rows) {
                if (error) return reject(error);
                resolve(method === 'run' ? { lastID: this.lastID, changes: this.changes } : rows);
            });
        })]));
    function enqueue(operation) {
        if (closing) return Promise.reject(new Error('Banco fechado'));
        const result = tail.then(operation);
        tail = result.catch(() => {});
        return result;
    }
    return {
        ...Object.fromEntries(['run', 'get', 'all'].map(method => [method, (sql, params) => enqueue(() => raw[method](sql, params))])),
        read: operation => enqueue(() => operation(raw)),
        transaction: operation => enqueue(async () => {
            await raw.run('BEGIN IMMEDIATE');
            try {
                const result = await operation(raw);
                await raw.run('COMMIT');
                return result;
            } catch (error) {
                try { await raw.run('ROLLBACK'); } catch (rollbackError) { error.rollbackError = rollbackError; }
                throw error;
            }
        }),
        async close() {
            if (closing) return tail;
            closing = true;
            const drained = tail.then(() => new Promise((resolve, reject) => connection.close(error => error ? reject(error) : resolve())));
            tail = drained;
            return drained;
        }
    };
}

async function initialize(database) {
    await database.transaction(async tx => {
        await tx.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT, active INTEGER NOT NULL DEFAULT 1, role TEXT NOT NULL DEFAULT \'user\')');
        const columns = await tx.all('PRAGMA table_info(users)');
        if (!columns.some(c => c.name === 'active')) await tx.run('ALTER TABLE users ADD COLUMN active INTEGER NOT NULL DEFAULT 1');
        if (!columns.some(c => c.name === 'role')) await tx.run("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'");
        await tx.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
        await tx.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
        await tx.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
        await tx.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
        await tx.run('CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id)');
        await tx.run('CREATE INDEX IF NOT EXISTS idx_payments_enrollment ON payments(enrollment_id)');
    });
}
async function seedDemo(database) {
    await database.transaction(async tx => {
        const existing = await tx.get('SELECT count(*) AS n FROM courses');
        if (existing.n) throw new Error('Demo exige banco sem cursos; nenhum dado foi apagado');
        const accounts = await tx.get('SELECT count(*) AS n FROM users');
        const enrollments = await tx.get('SELECT count(*) AS n FROM enrollments');
        const payments = await tx.get('SELECT count(*) AS n FROM payments');
        if (accounts.n || enrollments.n || payments.n) throw new Error('Demo exige banco vazio');
        await tx.run("INSERT INTO users(id,name,email,pass) VALUES (1,'Leonan','leonan@fullcycle.com.br',NULL)");
        await tx.run("INSERT INTO courses(id,title,price,active) VALUES (1,'Clean Architecture',997,1),(2,'Docker',497,1)");
        await tx.run('INSERT INTO enrollments(id,user_id,course_id) VALUES (1,1,1)');
        await tx.run("INSERT INTO payments(id,enrollment_id,amount,status) VALUES (1,1,997,'PAID')");
    });
}
module.exports = { openDatabase, initialize, seedDemo };
