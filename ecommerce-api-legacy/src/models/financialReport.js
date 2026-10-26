const { PAID } = require('../domain/paymentStatus');
async function financialReport(tx) {
    // LIMIT 1 follows the observed original SQLite get(), without multiplying
    // payments for historical duplicate rows. No public ordering is introduced.
    const rows = await tx.all(`SELECT c.id AS course_id,c.title,e.id AS enrollment_id,
        u.id AS user_id,u.name AS student,p.id AS payment_id,p.amount,p.status FROM courses c
        LEFT JOIN enrollments e ON e.course_id=c.id
        LEFT JOIN users u ON u.id=e.user_id
        LEFT JOIN payments p ON p.id=(SELECT p0.id FROM payments p0 WHERE p0.enrollment_id=e.id LIMIT 1)`);
    const report = new Map();
    for (const row of rows) {
        if (!report.has(row.course_id)) report.set(row.course_id, {course:row.title,revenue:0,students:[]});
        const course = report.get(row.course_id);
        if (row.enrollment_id === null) continue;
        if (row.status === PAID) course.revenue += row.amount;
        course.students.push({student: row.user_id === null ? 'Unknown' : row.student, paid:row.payment_id === null ? 0 : row.amount});
    }
    return [...report.values()];
}
module.exports = { financialReport };
