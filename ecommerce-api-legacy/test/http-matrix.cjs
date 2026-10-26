const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { fork, execFile } = require('node:child_process');
const { promisify } = require('node:util');
const run = promisify(execFile);
const { once } = require('node:events');
const { openDatabase } = require('../src/database');

async function main() {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'lms-http-'));
    const databasePath = path.join(directory, 'fixture.sqlite');
    const cwd = path.resolve(__dirname, '..');
    const password = 'Fixture💜-'+require('node:crypto').randomBytes(16).toString('hex');
    const env = {...process.env,LMS_DB:databasePath,LMS_PASSWORD:password};
    let child, database, exit, exitResult, ready;
    const evidence = { command:'npm run test:http', readinessTimeoutMs:10000, checks:[], boot:[], cleanup:false };
    const payload = extra=>({usr:'Áluna',eml:'aluna@test',pwd:password,c_id:2,card:'4111222233334444',...extra});
    try {
        await run(process.execPath,['scripts/seed-demo.cjs'],{cwd,env});
        await run(process.execPath,['scripts/account.cjs','create','admin@test','admin','Administrador'],{cwd,env});
        await run(process.execPath,['scripts/account.cjs','reset','leonan@fullcycle.com.br'],{cwd,env});
        child = fork(path.join(cwd,'src/server.js'),[],{cwd,env:{...env,PORT:'0',HOST:'127.0.0.1',LMS_DEMO:'0',LMS_PASSWORD:undefined},silent:true,windowsHide:true});
        exit = once(child,'exit').then(([code,signal])=>{exitResult={code,signal};return exitResult;});
        ready = await new Promise((resolve,reject)=>{
            let buffer='';
            const timeout=setTimeout(()=>reject(new Error('Readiness timeout')),10000);
            child.once('error',error=>{clearTimeout(timeout);reject(error);});
            child.once('exit',()=>{clearTimeout(timeout);reject(new Error('Process exited before readiness'));});
            child.stdout.on('data',chunk=>{
                buffer+=chunk;
                let end;
                while((end=buffer.indexOf('\n'))>=0){
                    const line=buffer.slice(0,end);buffer=buffer.slice(end+1);
                    evidence.boot.push(line);
                    try{const event=JSON.parse(line);if(event.event==='ready'){clearTimeout(timeout);resolve(event);}}catch{}
                }
            });
            child.stderr.on('data',chunk=>evidence.boot.push(String(chunk)));
        });
        assert.equal(ready.pid,child.pid);assert.ok(ready.port>0);
        evidence.pid=child.pid;evidence.port=ready.port;
        const base=`http://127.0.0.1:${ready.port}`;
        const call=async(method,url,expected,{body,identity,raw,authorization}={})=>{
            const response=await fetch(base+url,{method,headers:{
                ...(body!==undefined||raw!==undefined?{'Content-Type':'application/json'}:{}),
                ...(identity?{Authorization:'Basic '+Buffer.from(identity+':'+password).toString('base64')}:{}),
                ...(authorization?{Authorization:authorization}:{})
            },body:raw??(body===undefined?undefined:JSON.stringify(body)),signal:AbortSignal.timeout(5000)});
            const text=await response.text();assert.equal(response.status,expected,`${method} ${url}: ${text}`);
            evidence.checks.push({method,path:url,status:response.status});
            assert.ok(!text.includes('scrypt$')&&!text.includes(password)&&!text.includes('4111222233334444'));
            return {text,json:()=>JSON.parse(text)};
        };
        database=await openDatabase(databasePath);
        await call('GET','/api/admin/financial-report',401);
        await call('GET','/api/admin/financial-report',401,{authorization:'Bearer forged'});
        await call('GET','/api/admin/financial-report',401,{authorization:'Basic !!!'});
        await call('GET','/api/admin/financial-report',401,{authorization:'Basic '+Buffer.from('admin@test:wrong').toString('base64')});
        await call('GET','/api/admin/financial-report',403,{identity:'leonan@fullcycle.com.br'});
        const initial=(await call('GET','/api/admin/financial-report',200,{identity:'admin@test'})).json();
        assert.deepEqual(initial.find(c=>c.course==='Docker'),{course:'Docker',revenue:0,students:[]});
        assert.deepEqual(initial.find(c=>c.course==='Clean Architecture'),{course:'Clean Architecture',revenue:997,students:[{student:'Leonan',paid:997}]});
        await call('POST','/api/checkout',400,{body:payload({pwd:null})});
        await call('POST','/api/checkout',400,{body:payload({card:123})});
        await call('POST','/api/checkout',400,{body:payload({c_id:true})});
        await call('POST','/api/checkout',400,{raw:'{"broken":'});
        await call('POST','/api/checkout',404,{body:payload({c_id:999})});
        await call('POST','/api/checkout',400,{body:payload({eml:'denied@test',card:'5'})});
        assert.equal((await database.get("SELECT count(*) AS n FROM users WHERE email='denied@test'")).n,0);
        await call('POST','/api/checkout',401,{body:payload({eml:'leonan@fullcycle.com.br',pwd:'wrong'})});
        const success=(await call('POST','/api/checkout',200,{body:payload()})).json();
        assert.equal(success.msg,'Sucesso');assert.equal(typeof success.enrollment_id,'number');
        const account=await database.get("SELECT id FROM users WHERE email='aluna@test'");
        await call('POST','/api/checkout',200,{body:payload()});
        await Promise.all(Array.from({length:6},()=>call('POST','/api/checkout',200,{body:payload({eml:'concurrent@test'})})));
        assert.equal((await database.get("SELECT count(*) AS n FROM users WHERE email='concurrent@test'")).n,1);
        for(const table of ['users','enrollments','payments','audit_logs']){
            const before=await database.get('SELECT count(*) AS n,sum(amount) AS total FROM payments');
            await database.run(`CREATE TRIGGER forced_failure BEFORE INSERT ON ${table} BEGIN SELECT RAISE(ABORT,'test'); END`);
            await call('POST','/api/checkout',500,{body:payload({eml:'failure-'+table+'@test'})});
            await database.run('DROP TRIGGER forced_failure');
            assert.deepEqual(await database.get('SELECT count(*) AS n,sum(amount) AS total FROM payments'),before);
            assert.equal((await database.get('SELECT count(*) AS n FROM users WHERE email=?',['failure-'+table+'@test'])).n,0);
        }
        await call('DELETE','/api/users/'+account.id,401);
        await call('DELETE','/api/users/'+account.id,403,{identity:'leonan@fullcycle.com.br'});
        await call('DELETE','/api/users/NaN',400,{identity:'admin@test'});
        await call('POST','/api/checkout',200,{body:payload({eml:'race@test'})});
        const race=await database.get("SELECT id FROM users WHERE email='race@test'");
        await Promise.all([
            call('DELETE','/api/users/'+race.id,200,{identity:'admin@test'}),
            (async()=>{
                // Either request can acquire the writer first. Both valid outcomes
                // must preserve a linked row; no orphan/partial payment is accepted.
                const response=await fetch(base+'/api/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload({eml:'race@test'}))});
                assert.ok([200,403].includes(response.status));await response.text();
                evidence.checks.push({method:'POST',path:'/api/checkout',status:response.status,scenario:'concurrent deletion'});
            })()
        ]);
        assert.equal((await database.get('SELECT active FROM users WHERE id=?',[race.id])).active,0);
        const history=await database.get('SELECT count(*) AS n,sum(amount) AS total FROM payments');
        assert.equal((await call('DELETE','/api/users/'+account.id,200,{identity:'aluna@test'})).text,'Usuário removido.');
        assert.equal((await database.get('SELECT active FROM users WHERE id=?',[account.id])).active,0);
        assert.deepEqual(await database.get('SELECT count(*) AS n,sum(amount) AS total FROM payments'),history);
        await call('POST','/api/checkout',403,{body:payload()});
        await call('DELETE','/api/users/'+account.id,403,{identity:'aluna@test'});
        await call('DELETE','/api/users/'+account.id,200,{identity:'admin@test'});
        await run(process.execPath,['scripts/account.cjs','create','unlinked@test'],{cwd,env});
        const unlinked=await database.get("SELECT id FROM users WHERE email='unlinked@test'");
        await call('DELETE','/api/users/'+unlinked.id,200,{identity:'unlinked@test'});
        assert.equal(await database.get('SELECT id FROM users WHERE id=?',[unlinked.id]),undefined);
        await call('DELETE','/api/users/99999',200,{identity:'admin@test'});
        await database.run("UPDATE users SET role='user' WHERE email='admin@test'");
        await call('GET','/api/admin/financial-report',403,{identity:'admin@test'});
        await database.run("UPDATE users SET role='admin' WHERE email='admin@test'");
        await database.run("UPDATE users SET active=0 WHERE email='admin@test'");
        await call('GET','/api/admin/financial-report',403,{identity:'admin@test'});
        await database.run("UPDATE users SET active=1 WHERE email='admin@test'");
        await call('GET','/api/admin/financial-report',200,{identity:'admin@test'});
        await call('GET','/does-not-exist',404);
        await call('POST','/api/admin/financial-report',404);
        const orphans=await database.get('SELECT count(*) AS n FROM enrollments e LEFT JOIN users u ON u.id=e.user_id WHERE u.id IS NULL');
        assert.equal(orphans.n,0);
        assert.ok(!evidence.boot.join('\n').includes(password)&&!evidence.boot.join('\n').includes('4111222233334444'));
    } finally {
        if(database)await database.close();
        if(child){
            if(child.connected)child.send('shutdown');
            let timer;
            const timedOut=await Promise.race([exit.then(()=>false),new Promise(resolve=>{timer=setTimeout(()=>resolve(true),5000);})]);
            clearTimeout(timer);
            if(timedOut){child.kill();await exit;throw new Error('Graceful shutdown timed out; owned child terminated');}
            assert.equal(exitResult.code,0,'Child must exit cleanly');
            evidence.exit=exitResult;
        }
        assert.ok(path.resolve(directory).startsWith(path.resolve(os.tmpdir())+path.sep));
        await fs.rm(directory,{recursive:true,force:true});
        evidence.cleanup=true;
    }
    evidence.result='PASS';evidence.endpointCount=3;evidence.caseCount=evidence.checks.length;
    console.log(JSON.stringify(evidence,null,2));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
