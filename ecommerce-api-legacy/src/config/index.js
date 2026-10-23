function loadConfig(env = process.env) {
  const authSecret = env.AUTH_SECRET;
  if (typeof authSecret !== 'string' || Buffer.byteLength(authSecret) < 32) throw new Error('AUTH_SECRET must contain at least 32 bytes');
  const port = Number(env.PORT ?? 3000);
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT must be 0..65535');
  const tokenTtlSeconds = Number(env.TOKEN_TTL_SECONDS ?? 3600);
  if (!Number.isInteger(tokenTtlSeconds) || tokenTtlSeconds < 1 || tokenTtlSeconds > 86400) throw new Error('TOKEN_TTL_SECONDS must be 1..86400');
  const demoSeed = env.DEMO_SEED === 'true';
  const adminEmail = env.DEMO_ADMIN_EMAIL;
  const adminPassword = env.DEMO_ADMIN_PASSWORD;
  if (demoSeed && (typeof adminEmail !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(adminEmail) || typeof adminPassword !== 'string' || adminPassword.length < 8 || adminPassword.length > 256)) throw new Error('DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD (8..256 characters) are required for DEMO_SEED');
  return { authSecret, port, tokenTtlSeconds, databasePath: env.DB_PATH || ':memory:', demoSeed, adminEmail, adminPassword };
}
module.exports = { loadConfig };
