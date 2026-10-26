const test=require('node:test');
const assert=require('node:assert/strict');
const {fixture,checkout}=require('./support.cjs');
async function account(f,email,role='user') {
 const {hashPassword}=require('../src/security/passwords');
 const pass=await hashPassword('Senha💜completa');
 const result=await f.database.run('INSERT INTO users(name,email,pass,role,active) VALUES (?,?,?,?,1)',[email,email,pass,role]);
 return {id:result.lastID,auth:email+':Senha💜completa'};
}
test('E03 salts, full Unicode password and no truncated fallback',async()=>{
 const {hashPassword,verifyPassword}=require('../src/security/passwords');
 const a=await hashPassword('ábc💜'),b=await hashPassword('ábc💜');
 assert.notEqual(a,b); assert.equal(await verifyPassword(a,'ábc💜'),true);
 assert.equal(await verifyPassword(a,'ábc💙'),false);
 assert.equal(await verifyPassword('YWYWYWYWYW','abc'),false);
 assert.equal(await verifyPassword('123','123'),false);
});
test('E04/E07 Basic current role, ownership and working physical/deactivation deletion',async()=>{
 const f=await fixture(); try {
  const admin=await account(f,'admin@test','admin'),owner=await account(f,'owner@test'),other=await account(f,'other@test');
  assert.equal((await f.request('/api/admin/financial-report',{auth:owner.auth})).status,403);
  assert.equal((await f.request('/api/admin/financial-report',{auth:'admin@test:wrong'})).status,401);
  assert.equal((await f.request('/api/admin/financial-report',{auth:admin.auth})).status,200);
  assert.equal((await f.request('/api/users/'+owner.id,{method:'DELETE',auth:other.auth})).status,403);
  assert.equal((await f.request('/api/users/'+owner.id,{method:'DELETE',auth:owner.auth})).text,'Usuário removido.');
  assert.equal(await f.database.get('SELECT * FROM users WHERE id=?',[owner.id]),undefined);
  const before=await f.database.get('SELECT count(*) AS n,sum(amount) AS total FROM payments');
  assert.equal((await f.request('/api/users/1',{method:'DELETE',auth:admin.auth})).status,200);
  assert.equal((await f.database.get('SELECT active FROM users WHERE id=1')).active,0);
  assert.deepEqual(await f.database.get('SELECT count(*) AS n,sum(amount) AS total FROM payments'),before);
  assert.equal((await f.database.get('SELECT name FROM users WHERE id=1')).name,'Leonan');
  assert.equal((await f.request('/api/users/1',{method:'DELETE',auth:admin.auth})).status,200);
  assert.equal((await f.request('/api/users/999',{method:'DELETE',auth:admin.auth})).status,200);
  await f.database.run("UPDATE users SET role='user' WHERE id=?",[admin.id]);
  assert.equal((await f.request('/api/admin/financial-report',{auth:admin.auth})).status,403);
  await f.database.run('UPDATE users SET active=0 WHERE id=?',[other.id]);
  assert.equal((await f.request('/api/users/'+other.id,{method:'DELETE',auth:other.auth})).status,403);
 } finally {await f.close();}
});
test('E05 full checkout transaction rolls back every required write',async()=>{
 for(const table of ['users','enrollments','payments','audit_logs']) {
  const f=await fixture(); try {
   await f.database.run(`CREATE TRIGGER fail_write BEFORE INSERT ON ${table} BEGIN SELECT RAISE(ABORT,'fixture failure'); END`);
   const counts=async()=>Promise.all(['users','enrollments','payments','audit_logs'].map(t=>f.database.get(`SELECT count(*) AS n FROM ${t}`)));
   const before=await counts();
   const response=await f.request('/api/checkout',{method:'POST',body:checkout()});
   assert.equal(response.status,500,table);
   assert.equal(response.text,{users:'Erro ao criar usuário',enrollments:'Erro Matrícula',payments:'Erro Pagamento',audit_logs:'Erro DB'}[table]);
   assert.deepEqual(await counts(),before,table);
  } finally {await f.close();}
 }
});
test('E05 serialized concurrent checkout reuses account and preserves each payment',async()=>{
 const f=await fixture(); try {
  const responses=await Promise.all(Array.from({length:8},()=>f.request('/api/checkout',{method:'POST',body:checkout()})));
  assert.deepEqual(responses.map(r=>r.status),Array(8).fill(200));
  assert.equal((await f.database.get('SELECT count(*) AS n FROM users WHERE email=?',['aluna@example.test'])).n,1);
  assert.equal((await f.database.get('SELECT count(*) AS n FROM payments')).n,9);
  assert.equal((await f.database.get('SELECT count(*) AS n FROM audit_logs')).n,8);
 } finally {await f.close();}
});
test('E08 financial shape, absent relations, nonpaid amount and first payment parity',async()=>{
 const f=await fixture(); try {
  const admin=await account(f,'admin@test','admin');
  await f.database.run("INSERT INTO courses(id,title,price,active) VALUES (3,'Inativo',0,0)");
  await f.database.run('INSERT INTO enrollments(id,user_id,course_id) VALUES (2,999,2),(3,999,2),(4,999,2)');
  await f.database.run("INSERT INTO payments(enrollment_id,amount,status) VALUES (2,10,'DENIED'),(3,5,'PAID'),(3,900,'PAID')");
  const report=(await f.request('/api/admin/financial-report',{auth:admin.auth})).json();
  assert.equal(report.length,3);
  assert.deepEqual(report.find(c=>c.course==='Inativo'),{course:'Inativo',revenue:0,students:[]});
  assert.deepEqual(report.find(c=>c.course==='Docker'),{course:'Docker',revenue:5,students:[{student:'Unknown',paid:10},{student:'Unknown',paid:5},{student:'Unknown',paid:0}]});
  assert.deepEqual(report.find(c=>c.course==='Clean Architecture'),{course:'Clean Architecture',revenue:997,students:[{student:'Leonan',paid:997}]});
 } finally {await f.close();}
});
test('E10 invalid/missing/null inputs are controlled and valid existing checkout works',async()=>{
 const f=await fixture(); try {
  for(const body of [null,[],{},checkout({pwd:null}),checkout({card:123}),checkout({c_id:true}),checkout({c_id:0}),checkout({usr:''}),checkout({eml:{}})])
   assert.equal((await f.request('/api/checkout',{method:'POST',body})).status,400,JSON.stringify(body));
  assert.equal((await f.request('/api/checkout',{method:'POST',body:checkout({c_id:999})})).status,404);
  assert.equal((await f.request('/api/checkout',{method:'POST',body:checkout()})).status,200);
  assert.equal((await f.request('/api/checkout',{method:'POST',body:checkout()})).status,200);
  const admin=await account(f,'admin@test','admin');
  assert.equal((await f.request('/api/users/NaN',{method:'DELETE',auth:admin.auth})).status,400);
  assert.equal((await f.request('/api/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:'bad'})).status,400);
 } finally {await f.close();}
});
test('E06/E05 explicit transaction rollback and queued reads never see partial state',async()=>{
 const f=await fixture(); try {
  let release;const gate=new Promise(r=>{release=r;});
  const writing=f.database.transaction(async tx=>{await tx.run("INSERT INTO users(name,email) VALUES ('pending','pending@test')");await gate;throw Error('rollback');});
  const reading=f.database.get("SELECT count(*) AS n FROM users WHERE email='pending@test'");
  release(); await assert.rejects(writing,/rollback/); assert.equal((await reading).n,0);
 } finally {await f.close();}
});
module.exports={account};
