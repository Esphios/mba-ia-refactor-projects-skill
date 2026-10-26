const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {promisify}=require('node:util');
const execFile=promisify(require('node:child_process').execFile);
const {fixture,checkout}=require('./support.cjs');

test('E05 commit failure rolls back user/enrollment/payment/audit, not only a write failure',async()=>{
 const f=await fixture();try{
  await f.database.run('PRAGMA foreign_keys=ON');
  await f.database.run('CREATE TABLE parent(id INTEGER PRIMARY KEY)');
  await f.database.run('CREATE TABLE child(id INTEGER REFERENCES parent(id) DEFERRABLE INITIALLY DEFERRED)');
  await f.database.run('CREATE TRIGGER deferred_failure AFTER INSERT ON audit_logs BEGIN INSERT INTO child VALUES (99); END');
  const response=await f.request('/api/checkout',{method:'POST',body:checkout()});
  assert.equal(response.status,500);
  assert.equal((await f.database.get('SELECT count(*) AS n FROM users')).n,1);
  assert.equal((await f.database.get('SELECT count(*) AS n FROM enrollments')).n,1);
  assert.equal((await f.database.get('SELECT count(*) AS n FROM payments')).n,1);
  assert.equal((await f.database.get('SELECT count(*) AS n FROM audit_logs')).n,0);
  assert.equal((await f.database.get('SELECT count(*) AS n FROM child')).n,0);
 }finally{await f.close();}
});
test('E08 report performs one SELECT with 1 and 20 enrollments',async()=>{
 const {financialReport}=require('../src/models/financialReport');
 const f=await fixture();try{
  for(const size of [1,20]){
   await f.database.run('DELETE FROM enrollments');
   for(let i=0;i<size;i++)await f.database.run('INSERT INTO enrollments(user_id,course_id) VALUES (1,1)');
   let count=0;
   const report=await f.database.read(tx=>financialReport({all:(sql,params)=>{count++;return tx.all(sql,params);}}));
   assert.equal(count,1);assert.equal(report.find(c=>c.course==='Clean Architecture').students.length,size);
  }
 }finally{await f.close();}
});
test('E03 migration preserves legacy financial data; operational reset rejects prefixes and changes full password',async()=>{
 const directory=await fs.mkdtemp(path.join(os.tmpdir(),'lms-migration-'));
 const filename=path.join(directory,'legacy.sqlite');
 const {openDatabase}=require('../src/database');
 const {createApplication}=require('../src/app');
 let db=await openDatabase(filename),application;
 try{
  await db.run('CREATE TABLE users(id INTEGER PRIMARY KEY,name TEXT,email TEXT,pass TEXT)');
  await db.run("INSERT INTO users VALUES (1,'Legado','legado@test','YWYWYWYWYW')");
  await db.run('CREATE TABLE payments(id INTEGER PRIMARY KEY,enrollment_id INTEGER,amount REAL,status TEXT)');
  await db.run("INSERT INTO payments VALUES (1,99,123.5,'PAID')");
  await db.close();db=null;
  application=await createApplication({databasePath:filename});
  assert.deepEqual(await application.database.get('SELECT * FROM payments'),{id:1,enrollment_id:99,amount:123.5,status:'PAID'});
  assert.equal((await application.database.get('SELECT active FROM users')).active,1);
  const {verifyPassword}=require('../src/security/passwords');
  assert.equal(await verifyPassword((await application.database.get('SELECT pass FROM users')).pass,'abc'),false);
  await application.close();application=null;
  const result=await execFile(process.execPath,['scripts/account.cjs','reset','legado@test'],{cwd:path.join(__dirname,'..'),env:{...process.env,LMS_DB:filename,LMS_PASSWORD:'nova💜Senha'}});
  assert.ok(!result.stdout.includes('nova💜Senha'));
  application=await createApplication({databasePath:filename});
  const stored=(await application.database.get('SELECT pass FROM users')).pass;
  assert.equal(await verifyPassword(stored,'nova💜Senha'),true);
  assert.equal(await verifyPassword(stored,'nova💜Errada'),false);
  assert.equal((await application.database.get('SELECT count(*) AS n FROM payments')).n,1);
 }finally{if(db)await db.close();if(application)await application.close();await fs.rm(directory,{recursive:true,force:true});}
});
test('E06 invalid database path fails initialization without listening',async()=>{
 const {createApplication}=require('../src/app');
 await assert.rejects(createApplication({databasePath:path.join(os.tmpdir(),'nonexistent-lms-parent-'+process.pid,'db.sqlite')}));
});
test('E09 database failures in report/course/deletion return controlled errors without false success',async()=>{
 const {hashPassword}=require('../src/security/passwords');
 const f=await fixture();try{
  const hash=await hashPassword('test-password');
  await f.database.run("INSERT INTO users(name,email,pass,role) VALUES ('Admin','admin@test',?,'admin')",[hash]);
  await f.database.run("CREATE TRIGGER prevent_deactivation BEFORE UPDATE ON users WHEN NEW.active=0 BEGIN SELECT RAISE(ABORT,'private database detail'); END");
  const deletion=await f.request('/api/users/1',{method:'DELETE',auth:'admin@test:test-password'});
  assert.equal(deletion.status,500);assert.equal(deletion.text,'Erro DB');
  assert.equal((await f.database.get('SELECT active FROM users WHERE id=1')).active,1);
  await f.database.run('DROP TABLE courses');
  const report=await f.request('/api/admin/financial-report',{auth:'admin@test:test-password'});
  assert.equal(report.status,500);assert.equal(report.text,'Erro DB');
  assert.equal((await f.request('/api/checkout',{method:'POST',body:checkout()})).status,500);
 }finally{await f.close();}
});
test('E08 empty database report and null legacy amounts retain JSON semantics',async()=>{
 const {financialReport}=require('../src/models/financialReport');
 const f=await fixture();try{
  await f.database.run('DELETE FROM courses');
  assert.deepEqual(await f.database.read(financialReport),[]);
  await f.database.run("INSERT INTO courses VALUES (1,'Grátis',0,1)");
  await f.database.run('UPDATE payments SET amount=NULL WHERE id=1');
  assert.deepEqual(await f.database.read(financialReport),[{course:'Grátis',revenue:0,students:[{student:'Leonan',paid:null}]}]);
  await f.database.run('UPDATE payments SET amount=0 WHERE id=1');
  assert.deepEqual(await f.database.read(financialReport),[{course:'Grátis',revenue:0,students:[{student:'Leonan',paid:0}]}]);
 }finally{await f.close();}
});

test('E07 orphan financial history stays Unknown when checkout creates a user',async()=>{
 const f=await fixture();try{
  await f.database.run('DELETE FROM payments');
  await f.database.run('DELETE FROM enrollments');
  await f.database.run('DELETE FROM users');
  await f.database.run('INSERT INTO enrollments(id,user_id,course_id) VALUES (2,2,1)');
  await f.database.run("INSERT INTO payments(enrollment_id,amount,status) VALUES (2,123,'PAID')");
  const response=await f.request('/api/checkout',{method:'POST',body:checkout({c_id:1})});
  assert.equal(response.status,200);
  const created=await f.database.get('SELECT id FROM users WHERE email=?',['aluna@example.test']);
  assert.ok(created.id>2);
  const report=(await f.request('/api/admin/financial-report',{auth:'admin@test:test-password'}));
  // Add an admin only after exercising checkout; its id must also skip the orphan.
  assert.equal(report.status,401);
  const {hashPassword}=require('../src/security/passwords');
  await f.database.run("INSERT INTO users(id,name,email,pass,role) VALUES (99,'Admin','admin@test',?,'admin')",[await hashPassword('test-password')]);
  const rows=(await f.request('/api/admin/financial-report',{auth:'admin@test:test-password'})).json();
  const students=rows.find(row=>row.course==='Clean Architecture').students;
  assert.ok(students.some(row=>row.student==='Unknown'&&row.paid===123));
  assert.ok(students.some(row=>row.student==='Áluna'));
 }finally{await f.close();}
});

test('E07 account create skips user ids referenced by orphan enrollments',async()=>{
 const directory=await fs.mkdtemp(path.join(os.tmpdir(),'lms-orphan-account-'));
 const filename=path.join(directory,'database.sqlite');
 const {openDatabase,initialize}=require('../src/database');
 let database=await openDatabase(filename);
 try{
  await initialize(database);
  await database.run('INSERT INTO courses(id,title,price,active) VALUES (1,\'Course\',1,1)');
  await database.run('INSERT INTO enrollments(id,user_id,course_id) VALUES (1,7,1)');
  await database.close();database=null;
  await execFile(process.execPath,['scripts/account.cjs','create','admin@test','admin','Admin'],{
   cwd:path.join(__dirname,'..'),env:{...process.env,LMS_DB:filename,LMS_PASSWORD:'senha-admin-completa'}});
  database=await openDatabase(filename);
  const account=await database.get('SELECT id FROM users WHERE email=?',['admin@test']);
  assert.ok(account.id>7);
 }finally{if(database)await database.close();await fs.rm(directory,{recursive:true,force:true});}
});

test('E07 checkout skips enrollment ids referenced by orphan payments',async()=>{
 const {financialReport}=require('../src/models/financialReport');
 const f=await fixture();try{
  await f.database.run("INSERT INTO payments(enrollment_id,amount,status) VALUES (2,777,'PAID')");
  const response=await f.request('/api/checkout',{method:'POST',body:checkout()});
  assert.equal(response.status,200);
  assert.ok(response.json().enrollment_id>2);
  const docker=(await f.database.read(financialReport)).find(row=>row.course==='Docker');
  assert.equal(docker.revenue,497);
  assert.deepEqual(docker.students,[{student:'Áluna',paid:497}]);
  assert.deepEqual(await f.database.get('SELECT amount,status FROM payments WHERE enrollment_id=2'),
   {amount:777,status:'PAID'});
 }finally{await f.close();}
});
