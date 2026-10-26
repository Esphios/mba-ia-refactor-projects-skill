const { once } = require('node:events');
const { loadConfig } = require('./config');
const { createApplication } = require('./app');
async function start(config=loadConfig()) {
    const application = await createApplication(config);
    const server = application.app.listen(config.port,config.host);
    try { await once(server,'listening'); }
    catch (error) { await application.close(); throw error; }
    console.log(JSON.stringify({event:'ready',pid:process.pid,port:server.address().port}));
    let stopped;
    const stop = () => stopped ||= (async()=>{
        await new Promise((resolve,reject)=>server.close(error=>error?reject(error):resolve()));
        await application.close();
    })();
    return {server,stop};
}
if (require.main === module) {
    start().then(({stop})=>{
        const shutdown=()=>stop().then(()=>{if(process.connected)process.disconnect();process.exitCode=0;},()=>{if(process.connected)process.disconnect();process.exitCode=1;});
        process.once('SIGTERM',shutdown); process.once('SIGINT',shutdown);
        if(process.send) process.on('message',message=>{if(message==='shutdown')shutdown();});
    }).catch(()=>{console.error('Falha ao iniciar LMS');process.exitCode=1;});
}
module.exports = { start };
