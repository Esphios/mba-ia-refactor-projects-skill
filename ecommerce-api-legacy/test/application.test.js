const { test }=require('node:test');
const assert=require('node:assert/strict');
const { createApplication }=require('../src/app');
const { hashPassword, verifyPassword }=require('../src/security/passwords');
const { loadConfig }=require('../src/config');
const config={authSecret:'test-only-cryptographically-long-secret-123456789',tokenTtlSeconds:60,databasePath:':memory:',demoSeed:true,adminEmail:'admin@example.test',adminPassword:'admin-fixture-password',port:0};
async function fixture(t,extra={}) {
 const logs=[]; const instance=await createApplication({config:{...config,...extra},logger:event=>logs.push(event)});
 const server=instance.app.listen(0,'127.0.0.1');await new Promise(r=>server.once('listening',r));
 t.after(async()=>{await new Promise(r=>server.close(r));await instance.close();});
 const call=async(path,method='GET',body,token)=>{
  const response=await fetch(`http://127.0.0.1:${server.address().port}${path}`,{method,headers:{'content-type':'application/json',...(token?{authorization:`Bearer ${token}`}:{})},body:body===undefined?undefined:JSON.stringify(body)});
  const text=await response.text(); let data;try{data=JSON.parse(text);}catch{data=text;}
  return {status:response.status,data};
 };
 const login=async(email=config.adminEmail,password=config.adminPassword)=>call('/api/auth/login','POST',{email,password});
 return {...instance,call,login,logs};
}
const input=(email='student@example.test')=>({usr:'Student',eml:email,pwd:'student-password',c_id:1,card:'4111111111111111'});
async function counts(db){return db.read(async tx=>{const result={};for(const table of ['users','enrollments','payments','audit_logs'])result[table]=(await tx.get(`SELECT COUNT(*) n FROM ${table}`)).n;return result;});}

test('external configuration validates required signing secret, seed credentials, TTL and port',()=>{
 assert.throws(()=>loadConfig({}),/AUTH_SECRET/);
 assert.throws(()=>loadConfig({AUTH_SECRET:'short'}),/AUTH_SECRET/);
 assert.throws(()=>loadConfig({AUTH_SECRET:config.authSecret,DEMO_SEED:'true'}),/ADMIN/);
 assert.throws(()=>loadConfig({AUTH_SECRET:config.authSecret,PORT:'bad'}),/PORT/);
 assert.throws(()=>loadConfig({AUTH_SECRET:config.authSecret,TOKEN_TTL_SECONDS:'0'}),/TOKEN/);
});
test('salted password storage rejects incorrect password and malformed legacy values',async()=>{
 const a=await hashPassword('same-password'),b=await hashPassword('same-password');
 assert.notEqual(a,b);assert.equal(await verifyPassword('same-password',a),true);
 assert.equal(await verifyPassword('wrong-password',a),false);assert.equal(await verifyPassword('123','123'),false);
 assert.equal(await verifyPassword('x','scrypt$broken'),false);
});
test('all checkout boundaries, success shapes, identity proof, refusal and safe logs',async t=>{
 const f=await fixture(t);const baseline=await counts(f.db);
 for(const body of [{},{...input(),card:42},{...input(),usr:[]},{...input(),eml:'bad'}, {...input(),c_id:'1 OR 1=1'}, {...input(),pwd:undefined}, {...input(),c_id:1.5}, {...input(),pwd:''}])assert.equal((await f.call('/api/checkout','POST',body)).status,400);
 assert.equal((await f.call('/api/checkout','POST',{...input(),c_id:999})).status,404);
 const denied=await f.call('/api/checkout','POST',{...input(),card:'5111111111111111'});assert.deepEqual(denied,{status:400,data:'Pagamento recusado'});assert.deepEqual(await counts(f.db),baseline);
 const paid=await f.call('/api/checkout','POST',input());assert.equal(paid.status,200);assert.deepEqual(Object.keys(paid.data).sort(),['enrollment_id','msg']);assert.equal(paid.data.msg,'Sucesso');
 const user=await f.db.read(tx=>tx.get('SELECT * FROM users WHERE email=?',[input().eml]));assert.match(user.pass,/^scrypt\$/);assert.equal(user.role,'user');
 assert.equal((await f.call('/api/checkout','POST',{...input(),pwd:undefined})).status,401);
 assert.equal((await f.call('/api/checkout','POST',{...input(),pwd:'wrong-password'})).status,401);
 assert.equal((await f.call('/api/checkout','POST',input())).status,200);
 const token=(await f.login(input().eml,input().pwd)).data.access_token;
 assert.equal((await f.call('/api/checkout','POST',{...input(),pwd:undefined},token)).status,200);
 const newCounts=await counts(f.db);assert.equal(newCounts.users,baseline.users+1);assert.equal(newCounts.enrollments,baseline.enrollments+3);assert.equal(newCounts.audit_logs,baseline.audit_logs+3);
 assert.doesNotMatch(JSON.stringify(f.logs),/4111111111111111|student-password|test-only-cryptographically/);
});
test('login, authorization, forged/expired tokens and current role and active state',async t=>{
 const f=await fixture(t);
 for(const body of [{},{email:[],password:'x'}])assert.equal((await f.call('/api/auth/login','POST',body)).status,400);
 assert.equal((await f.login('missing@example.test','wrong-password')).status,401);assert.equal((await f.login(config.adminEmail,'wrong-password')).status,401);
 assert.equal((await f.call('/api/admin/financial-report')).status,401);
 assert.equal((await f.call('/api/users/1','DELETE')).status,401);
 const auth=await f.login();assert.equal(auth.status,200);assert.deepEqual(Object.keys(auth.data).sort(),['access_token','expires_in','token_type']);
 const token=auth.data.access_token;assert.equal((await f.call('/api/admin/financial-report','GET',undefined,token+'x')).status,401);
 const { issueToken }=require('../src/security/tokens');
 const expired=issueToken(1,config.authSecret,60,Math.floor(Date.now()/1000)-100);
 assert.equal((await f.call('/api/admin/financial-report','GET',undefined,expired)).status,401);
 assert.equal((await f.call('/api/admin/financial-report','GET',undefined,token)).status,200);
 await f.db.transaction(tx=>tx.run("UPDATE users SET role='user' WHERE email=?",[config.adminEmail]));
 assert.equal((await f.call('/api/admin/financial-report','GET',undefined,token)).status,403);
 await f.db.transaction(tx=>tx.run('UPDATE users SET active=0 WHERE email=?',[config.adminEmail]));
 assert.equal((await f.call('/api/admin/financial-report','GET',undefined,token)).status,401);
 assert.equal((await f.login()).status,401);
});
test('self/admin lifecycle deletes unreferenced users and deactivates referenced users preserving financial history',async t=>{
 const f=await fixture(t);await f.call('/api/checkout','POST',input());await f.call('/api/checkout','POST',input('other@example.test'));
 const user=await f.db.read(tx=>tx.get('SELECT id FROM users WHERE email=?',[input().eml]));
 const other=await f.db.read(tx=>tx.get('SELECT id FROM users WHERE email=?',['other@example.test']));
 const token=(await f.login(input().eml,input().pwd)).data.access_token;const admin=(await f.login()).data.access_token;
 assert.equal((await f.call(`/api/users/${other.id}`,'DELETE',undefined,token)).status,403);
 assert.equal((await f.call('/api/users/no','DELETE',undefined,admin)).status,400);assert.equal((await f.call('/api/users/9999','DELETE',undefined,admin)).status,404);
 const before=await counts(f.db);const response=await f.call(`/api/users/${user.id}`,'DELETE',undefined,token);assert.deepEqual(response,{status:200,data:{msg:'Usuário desativado; histórico financeiro preservado',id:user.id,action:'deactivated'}});
 assert.deepEqual(await counts(f.db),before);const retained=await f.db.read(tx=>tx.get('SELECT * FROM users WHERE id=?',[user.id]));assert.equal(retained.active,0);assert.equal(retained.name,'Student');
 assert.equal((await f.call(`/api/users/${user.id}`,'DELETE',undefined,token)).status,401);
 assert.equal((await f.call('/api/checkout','POST',input())).status,401);
 const id=await f.db.transaction(async tx=>(await tx.run('INSERT INTO users(name,email,pass,role,active) VALUES(?,?,?,\'user\',1)',['No history','unused@example.test',await hashPassword('unused-password')])).lastID);
 const unusedToken=(await f.login('unused@example.test','unused-password')).data.access_token;
 assert.equal((await f.call(`/api/users/${id}`,'DELETE',undefined,unusedToken)).data.action,'deleted');
 assert.equal(await f.db.read(tx=>tx.get('SELECT id FROM users WHERE id=?',[id])),undefined);
 assert.equal((await f.call(`/api/users/${other.id}`,'DELETE',undefined,admin)).data.action,'deactivated');
});
test('each write failure rolls back the entire checkout, and concurrent operations stay isolated',async t=>{
 const f=await fixture(t);const baseline=await counts(f.db);
 for(const table of ['users','enrollments','payments','audit_logs']){
  await f.db.transaction(tx=>tx.run(`CREATE TRIGGER fail_write BEFORE INSERT ON ${table} BEGIN SELECT RAISE(ABORT,'fixture failure'); END`));
  assert.equal((await f.call('/api/checkout','POST',input(`${table}@example.test`))).status,500);
  assert.deepEqual(await counts(f.db),baseline,table);
  await f.db.transaction(tx=>tx.run('DROP TRIGGER fail_write'));
 }
 const responses=await Promise.all(Array.from({length:12},(_,i)=>f.call('/api/checkout','POST',input(`concurrent${i}@example.test`))));assert.ok(responses.every(r=>r.status===200));
 const after=await counts(f.db);for(const table of Object.keys(after))assert.equal(after[table],baseline[table]+12,table);
 const same=await Promise.all(Array.from({length:4},()=>f.call('/api/checkout','POST',input('same@example.test'))));assert.ok(same.every(r=>r.status===200));
 assert.equal((await f.db.read(tx=>tx.get('SELECT COUNT(*) n FROM users WHERE email=?',['same@example.test']))).n,1);
});
test('database failures in lookup/report/delete return 500 without leaking SQL or claiming success',async t=>{
 const f=await fixture(t);const admin=(await f.login()).data.access_token;
 await f.db.transaction(tx=>tx.run("CREATE TRIGGER fail_delete BEFORE DELETE ON users BEGIN SELECT RAISE(ABORT,'secret fixture SQL'); END"));
 const result=await f.call('/api/users/1','DELETE',undefined,admin);assert.equal(result.status,500);assert.equal(result.data,'Erro DB');
 await f.db.transaction(tx=>tx.run('ALTER TABLE courses RENAME TO unavailable_courses'));
 assert.deepEqual(await f.call('/api/admin/financial-report','GET',undefined,admin),{status:500,data:'Erro DB'});
 assert.equal((await f.call('/api/checkout','POST',input())).status,500);
});
test('report constant query count, exact response shape, empty courses and paid/denied aggregation',async t=>{
 const f=await fixture(t);const token=(await f.login()).data.access_token;
 const measure=async()=>{f.db.resetQueryCount();const response=await f.call('/api/admin/financial-report','GET',undefined,token);return {response,count:f.db.queryCount};};
 await f.call('/api/checkout','POST',input());let measured=await measure();assert.equal(measured.response.status,200);const count=measured.count;
 assert.deepEqual(measured.response.data,[{course:'Clean Architecture',revenue:997,students:[{student:'Student',paid:997}]},{course:'Docker',revenue:0,students:[]}]);
 for(let i=0;i<19;i++)assert.equal((await f.call('/api/checkout','POST',input(`report${i}@example.test`))).status,200);
 measured=await measure();assert.equal(measured.count,count);assert.equal(count,2,'one auth lookup plus one joined report SELECT');assert.equal(measured.response.data[0].revenue,19940);
 await f.db.transaction(async tx=>{await tx.run("UPDATE payments SET status='DENIED' WHERE id=1");await tx.run('DELETE FROM payments WHERE id=2');});
 measured=await measure();assert.equal(measured.response.data[0].revenue,17946);assert.equal(measured.response.data[0].students[0].paid,997);assert.equal(measured.response.data[0].students[1].paid,0);
 await f.db.transaction(async tx=>{await tx.run('DELETE FROM payments');await tx.run('DELETE FROM enrollments');await tx.run('DELETE FROM courses');});
 assert.deepEqual((await measure()).response.data,[]);
 console.log(`QUERY_COUNT: 1 enrollment=${count}; 20 enrollments=${count}; includes current-user authentication`);
});
test('readiness fails cleanly for an existing legacy schema rather than reseeding or dropping data',async()=>{
 const sqlite3=require('sqlite3');const fs=require('node:fs/promises');const os=require('node:os');const path=require('node:path');
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'project2-legacy-'));const file=path.join(dir,'legacy.db');
 const db=new sqlite3.Database(file);await new Promise((resolve,reject)=>db.exec("CREATE TABLE users(id INTEGER PRIMARY KEY,name TEXT,email TEXT,pass TEXT); INSERT INTO users VALUES(7,'Legacy','legacy@example.test','plaintext');",e=>e?reject(e):resolve()));await new Promise(r=>db.close(r));
 try{await assert.rejects(createApplication({config:{...config,databasePath:file}}),/legacy|migration/i);
  const check=new sqlite3.Database(file);const row=await new Promise((r,j)=>check.get('SELECT * FROM users WHERE id=7',(e,x)=>e?j(e):r(x)));assert.equal(row.pass,'plaintext');await new Promise(r=>check.close(r));
 }finally{assert.equal(path.dirname(path.resolve(dir)),path.resolve(os.tmpdir()));await fs.rm(dir,{recursive:true});}
});

test('controlled legacy migration preserves records and finances, disables ambiguous credentials, and explicit reset enables login',async t=>{
 const { openDatabase }=require('../src/db/connection');const { migrateLegacy }=require('../src/db/migrate-legacy');const { resetPassword }=require('../src/db/reset-password');
 const db=await openDatabase(':memory:');t.after(()=>db.close());
 await db.transaction(async tx=>{
  for(const sql of ['CREATE TABLE users(id INTEGER PRIMARY KEY,name TEXT,email TEXT,pass TEXT)','CREATE TABLE courses(id INTEGER PRIMARY KEY,title TEXT,price REAL,active INTEGER)','CREATE TABLE enrollments(id INTEGER PRIMARY KEY,user_id INTEGER,course_id INTEGER)','CREATE TABLE payments(id INTEGER PRIMARY KEY,enrollment_id INTEGER,amount REAL,status TEXT)','CREATE TABLE audit_logs(id INTEGER PRIMARY KEY,action TEXT,created_at DATETIME)',"INSERT INTO users VALUES(7,'Legacy','legacy@example.test','123')","INSERT INTO courses VALUES(3,'History',123,1)",'INSERT INTO enrollments VALUES(9,7,3)',"INSERT INTO payments VALUES(11,9,123,'PAID')"])await tx.run(sql);
 });
 const before=await counts(db);await migrateLegacy(db);assert.deepEqual(await counts(db),before);
 let user=await db.read(tx=>tx.get('SELECT * FROM users WHERE id=7'));assert.equal(user.pass,'123');assert.equal(user.password_reset_required,1);assert.equal(user.role,'user');
 await migrateLegacy(db);assert.deepEqual(await counts(db),before);
 await resetPassword(db,'legacy@example.test','replacement-password');user=await db.read(tx=>tx.get('SELECT * FROM users WHERE id=7'));assert.equal(user.password_reset_required,0);assert.equal(await verifyPassword('replacement-password',user.pass),true);
 const { authService }=require('../src/services/authService');assert.equal((await authService(db,config,user.pass).login('legacy@example.test','replacement-password')).token_type,'Bearer');
 assert.deepEqual(await counts(db),before);assert.equal((await db.read(tx=>tx.get('SELECT amount FROM payments WHERE id=11'))).amount,123);
 await db.transaction(tx=>tx.run('INSERT INTO enrollments VALUES(10,999,3)'));
 const { financialReport }=require('../src/models/financialReportModel');assert.deepEqual(await db.read(financialReport),[{course:'History',revenue:123,students:[{student:'Legacy',paid:123},{student:'Unknown',paid:0}]}]);
});
test('startup against an existing current database never reseeds or overwrites rows',async t=>{
 const fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'project2-existing-'));const databasePath=path.join(dir,'current.db');
 try{let f=await createApplication({config:{...config,databasePath}});await f.db.transaction(tx=>tx.run("UPDATE users SET name='Preserved' WHERE id=1"));const before=await counts(f.db);await f.close();
  f=await createApplication({config:{...config,databasePath}});assert.deepEqual(await counts(f.db),before);assert.equal((await f.db.read(tx=>tx.get('SELECT name FROM users WHERE id=1'))).name,'Preserved');await f.close();
 }finally{assert.equal(path.dirname(path.resolve(dir)),path.resolve(os.tmpdir()));await fs.rm(dir,{recursive:true});}
});

test('concurrent failing and successful transactions do not share rollback state',async t=>{
 const f=await fixture(t);const before=await counts(f.db);
 await f.db.transaction(tx=>tx.run("CREATE TRIGGER conditional_failure BEFORE INSERT ON payments WHEN (SELECT u.email FROM enrollments e JOIN users u ON u.id=e.user_id WHERE e.id=NEW.enrollment_id)='fail@example.test' BEGIN SELECT RAISE(ABORT,'expected concurrent failure'); END"));
 const results=await Promise.all([f.call('/api/checkout','POST',input('fail@example.test')),f.call('/api/checkout','POST',input('ok@example.test'))]);assert.deepEqual(results.map(r=>r.status),[500,200]);
 const after=await counts(f.db);for(const table of Object.keys(after))assert.equal(after[table],before[table]+1,table);
 assert.equal(await f.db.read(tx=>tx.get('SELECT id FROM users WHERE email=?',['fail@example.test'])),undefined);
});
