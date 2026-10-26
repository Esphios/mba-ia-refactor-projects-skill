const { openDatabase, initialize } = require('../src/database');
const { hashPassword, validPassword } = require('../src/security/passwords');
const users = require('../src/models/users');
async function main() {
    const [action,email,role='user',name=email] = process.argv.slice(2);
    if (!['create','reset'].includes(action) || !email || !['user','admin'].includes(role) ||
        !validPassword(process.env.LMS_PASSWORD) || !process.env.LMS_DB || process.env.LMS_DB === ':memory:')
        throw new Error('Use LMS_DB persistente e LMS_PASSWORD; account create|reset email [user|admin] [nome]');
    const passwordHash=await hashPassword(process.env.LMS_PASSWORD);
    delete process.env.LMS_PASSWORD;
    const database=await openDatabase(process.env.LMS_DB);
    try {
        await initialize(database);
        await database.transaction(async tx=>{
            const rows=await tx.all('SELECT id FROM users WHERE email=?',[email]);
            if(action==='create'){
                if(rows.length)throw new Error('Conta já existe');
                await users.create(tx,name,email,passwordHash,role);
            }else{
                if(rows.length!==1)throw new Error('Reset exige exatamente uma conta');
                await tx.run('UPDATE users SET pass=? WHERE id=?',[passwordHash,rows[0].id]);
                // Reset never reactivates a retained/deactivated account or changes role.
            }
        });
        console.log('Credencial atualizada.');
    }finally{await database.close();}
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
