module.exports = {
  activeCourse: (tx, id) => tx.get('SELECT * FROM courses WHERE id=? AND active=1', [id]),
  enroll: (tx, userId, courseId) => tx.run('INSERT INTO enrollments(user_id,course_id) VALUES(?,?)', [userId, courseId]),
  pay: (tx, enrollmentId, amount) => tx.run("INSERT INTO payments(enrollment_id,amount,status) VALUES(?,?,'PAID')", [enrollmentId, amount]),
  audit: (tx, courseId, userId) => tx.run("INSERT INTO audit_logs(action,created_at) VALUES(?,datetime('now'))", [`Checkout curso ${courseId} por ${userId}`])
};
