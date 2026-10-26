module.exports = {
    course: (tx, id) => tx.get('SELECT id,title,price,active FROM courses WHERE id=? AND active=1', [id]),
    async enroll(tx, userId, courseId) {
        const row = await tx.get(`SELECT COALESCE(MAX(id),0)+1 AS id FROM (
            SELECT id FROM enrollments UNION ALL SELECT enrollment_id AS id FROM payments
        )`);
        await tx.run('INSERT INTO enrollments(id,user_id,course_id) VALUES (?,?,?)',
            [row.id,userId,courseId]);
        return row.id;
    },
    payment: (tx, enrollmentId, amount, status) => tx.run('INSERT INTO payments(enrollment_id,amount,status) VALUES (?,?,?)', [enrollmentId,amount,status]),
    audit: (tx, action) => tx.run("INSERT INTO audit_logs(action,created_at) VALUES (?,datetime('now'))", [action])
};
