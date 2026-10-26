const { openDatabase, initialize, seedDemo } = require('../src/database');
(async()=>{
    if(!process.env.LMS_DB || process.env.LMS_DB===':memory:')throw new Error('LMS_DB persistente obrigatório');
    const database=await openDatabase(process.env.LMS_DB);
    try{await initialize(database);await seedDemo(database);console.log('Demo criada sem credencial padrão.');}
    finally{await database.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
