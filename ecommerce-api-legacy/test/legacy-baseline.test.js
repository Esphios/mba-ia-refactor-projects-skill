const { test } = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const vm = require('node:vm');
const express = require('express');

test('original three HTTP contracts on a disposable in-memory database', async () => {
  const source = execFileSync('git', ['show', '6d1ce6248c3e956801010a89d8bdaab48029bf30:ecommerce-api-legacy/src/AppManager.js'], {encoding:'utf8'});
  const context = {module:{exports:{}}, require: name => name === './utils'
    ? { config:{paymentGatewayKey:'disposable'}, logAndCache(){}, badCrypto:()=> 'legacy' }
    : require(name), console:{log(){}}};
  vm.runInNewContext(source, context);
  const manager = new context.module.exports();
  manager.initDb();
  const query = sql => new Promise((resolve,reject) => manager.db.all(sql, (err,rows)=>err?reject(err):resolve(rows)));
  await query('SELECT * FROM payments');
  const app=express(); app.use(express.json()); manager.setupRoutes(app);
  const server=app.listen(0,'127.0.0.1'); await new Promise(resolve=>server.once('listening',resolve));
  const base=`http://127.0.0.1:${server.address().port}`;
  const call=(path,method='GET',body)=>fetch(base+path,{method,headers:{'content-type':'application/json'},body:body?JSON.stringify(body):undefined});
  try {
    const input={usr:'Fixture',eml:'fixture@example.test',pwd:'fixture-password',c_id:1,card:'4111111111111111'};
    let response=await call('/api/checkout','POST',input);
    assert.equal(response.status,200); assert.deepEqual(await response.json(),{msg:'Sucesso',enrollment_id:2});
    response=await call('/api/checkout','POST',{...input,eml:'denied@example.test',card:'5111111111111111'});
    assert.equal(response.status,400); assert.equal(await response.text(),'Pagamento recusado');
    assert.equal((await query("SELECT * FROM users WHERE email='denied@example.test'")).length,1,'characterizes original partial write');
    response=await call('/api/checkout','POST',{}); assert.equal(response.status,400); assert.equal(await response.text(),'Bad Request');
    response=await call('/api/checkout','POST',{...input,c_id:999}); assert.equal(response.status,404);
    response=await call('/api/admin/financial-report'); assert.equal(response.status,200);
    const report=await response.json(); assert.equal(report.find(r=>r.course==='Clean Architecture').revenue,1994);
    assert.deepEqual(Object.keys(report[0]).sort(),['course','revenue','students']);
    response=await call('/api/users/1','DELETE'); assert.equal(response.status,200);
    assert.match(await response.text(),/matrículas e pagamentos ficaram sujos/);
    assert.equal((await query('SELECT * FROM enrollments WHERE user_id=1')).length,1,'characterizes original orphan');
    console.log('BASELINE: all 3 original method/path pairs; paid/denied/missing/course absent/report/delete; unsafe side effects characterized; no external charges');
  } finally { await new Promise(resolve=>server.close(resolve)); await new Promise((resolve,reject)=>manager.db.close(err=>err?reject(err):resolve())); }
});
