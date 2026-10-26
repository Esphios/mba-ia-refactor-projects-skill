const test = require('node:test');
const assert = require('node:assert/strict');
const { fixture, checkout } = require('./support.cjs');

test('E04 financial report requires verified identity', async () => {
  const f = await fixture(); try {
    assert.equal((await f.request('/api/admin/financial-report')).status, 401);
  } finally { await f.close(); }
});
test('E04 existing checkout rejects wrong password without writing', async () => {
  const f = await fixture(); try {
    const before = await f.database.get('SELECT count(*) AS n FROM enrollments');
    const response = await f.request('/api/checkout', {method:'POST',body:checkout({eml:'leonan@fullcycle.com.br',pwd:'wrong'})});
    assert.equal(response.status, 401);
    assert.equal((await f.database.get('SELECT count(*) AS n FROM enrollments')).n, before.n);
  } finally { await f.close(); }
});
test('E05 payment denial does not create an account', async () => {
  const f = await fixture(); try {
    assert.equal((await f.request('/api/checkout', {method:'POST',body:checkout({card:'5111222233334444'})})).status,400);
    assert.equal((await f.database.get('SELECT count(*) AS n FROM users WHERE email=?',['aluna@example.test'])).n,0);
  } finally { await f.close(); }
});
test('E04 unauthenticated deletion cannot remove a linked account', async () => {
  const f = await fixture(); try {
    assert.equal((await f.request('/api/users/1',{method:'DELETE'})).status,401);
    assert.ok(await f.database.get('SELECT id FROM users WHERE id=1'));
  } finally { await f.close(); }
});
test('E01 checkout never logs the submitted card', async () => {
  const f = await fixture(); const logs=[]; const original=console.log;
  console.log=(...args)=>logs.push(args.join(' '));
  try {
    assert.equal((await f.request('/api/checkout',{method:'POST',body:checkout()})).status,200);
    assert.ok(!logs.join('\n').includes('4111222233334444'));
  } finally { console.log=original; await f.close(); }
});
