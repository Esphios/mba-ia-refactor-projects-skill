const express = require('express');
const { openDatabase, initialize, seedDemo } = require('./database');
const { registerRoutes } = require('./routes');
const { errorHandler } = require('./http/errors');
const { checkoutService } = require('./services/checkout');
const { deletionService } = require('./services/userDeletion');
const { checkoutController } = require('./controllers/checkout');
const { reportController } = require('./controllers/financialReport');
const { deletionController } = require('./controllers/users');
async function createApplication({databasePath=':memory:',demo=false}={}) {
    const database = await openDatabase(databasePath);
    try {
        await initialize(database);
        if (demo) await seedDemo(database);
        const app = express();
        app.disable('x-powered-by');
        app.use(express.json());
        registerRoutes(app,{
            checkout:checkoutController(checkoutService(database)),
            report:reportController(database),
            remove:deletionController(deletionService(database))
        });
        app.use(errorHandler);
        return {app,database,close:()=>database.close()};
    } catch (error) { await database.close(); throw error; }
}
module.exports = { createApplication };
