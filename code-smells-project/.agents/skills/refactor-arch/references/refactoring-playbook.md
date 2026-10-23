# Finding-to-transformation playbook

Use the matching identifier from [anti-patterns.md](anti-patterns.md) and apply
only approved findings. Examples isolate a boundary; adapt schema, dependencies,
response envelopes and permissions to the inspected project. Python connections
use standard SQLite DB-API. JavaScript uses CommonJS/Express.

## AP-01 — Bind SQL values

Before:

```python
def find_user(connection, email):
    return connection.execute(
        "SELECT id FROM users WHERE email = '" + email + "'").fetchone()
```

After:

```python
def find_user(connection, email):
    return connection.execute(
        "SELECT id FROM users WHERE email = ?", (email,)).fetchone()
```

Values remain data. Parameters cannot bind table names: validate identifiers
against a known set. An approved arbitrary-SQL admin console is a separate trust
boundary behind verified admin authorization. Verify malicious input cannot log
in, legitimate email works, and apostrophes survive round trip; also test the
admin console's authorized success and unauthorized denial.

## AP-02 — External configuration and safe serialization

Before:

```python
def health(user):
    return {"status": "ok", "secret_key": "fixed-key", "user": dict(user)}
```

After:

```python
import os

def load_config():
    return {"SECRET_KEY": os.environ["SECRET_KEY"]}

def health(user):
    return {"status": "ok", "user": {
        "id": user["id"], "name": user["name"]}}
```

Select response fields explicitly; passwords and hashes never belong in output.
Keep unrelated approved health fields and obtain approval for sensitive field
removal. Verify missing/configured startup, responses and captured logs with
sentinel secrets. Previously deployed secrets need separate rotation.

## AP-03 — Route, controller and model boundaries

Before:

```javascript
function register(app, db) {
  app.get('/products/:id', (req, res, next) => {
    db.get('SELECT id, name FROM products WHERE id = ?', [req.params.id],
      (error, product) => {
        if (error) return next(error);
        if (!product) return res.status(404).json({ error: 'Not found' });
        return res.json(product);
      });
  });
}
```

After (place model, controller and routing functions in their own modules):

```javascript
function productModel(db) {
  return {
    find(id, callback) {
      db.get('SELECT id, name FROM products WHERE id = ?', [id], callback);
    }
  };
}

function productController(products) {
  return {
    show(req, res, next) {
      products.find(req.params.id, (error, product) => {
        if (error) return next(error);
        if (!product) return res.status(404).json({ error: 'Not found' });
        return res.json(product);
      });
    }
  };
}

function register(app, controller) {
  app.get('/products/:id', controller.show);
}

function compose(app, db) {
  register(app, productController(productModel(db)));
}
```

The route maps HTTP, the controller chooses HTTP results and the model owns SQL.
Add services only for meaningful orchestration. Verify success, missing record
and database errors through the real route. Trace imports to ensure persistence
does not depend on request/response and preserve contractual envelopes/status.

## AP-04 — Password hashing and expiring signed tokens

Before:

```python
import hashlib

def password_hash(password):
    return hashlib.md5(password.encode()).hexdigest()

def issue_token(user_id, secret):
    return f"token-{user_id}"

def verify_token(token, secret, max_age=3600):
    return int(token.removeprefix("token-"))
```

After:

```python
import hashlib
import hmac
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

def password_hash(password):
    return generate_password_hash(password, method="scrypt")

def check_and_upgrade(stored, password, legacy_md5=False):
    if legacy_md5:
        valid = hmac.compare_digest(
            stored, hashlib.md5(password.encode()).hexdigest())
        return valid, password_hash(password) if valid else None
    return check_password_hash(stored, password), None

def issue_token(user_id, secret):
    signer = URLSafeTimedSerializer(secret, salt="access-token")
    return signer.dumps({"user_id": user_id})

def verify_token(token, secret, max_age=3600):
    signer = URLSafeTimedSerializer(secret, salt="access-token")
    return signer.loads(token, max_age=max_age)["user_id"]
```

Choose algorithms supported by the actual runtime. Legacy mode is an explicit
migration decision, never fallback after a modern hash fails. Persist the upgraded
hash in the login transaction. Load current active status/role after verification;
map signature/expiry failures to 401 centrally. Verify new/legacy/wrong passwords,
unique salts, persisted upgrade, tampered/expired tokens and disabled accounts.

## AP-05 — Authorize a verified identity

Before:

```javascript
function register(app, users) {
  app.delete('/users/:id', (req, res, next) => {
    users.remove(req.params.id, (error) => {
      if (error) return next(error);
      return res.json({ deleted: true });
    });
  });
}
```

After:

```javascript
function adminOnly(req, res, next) {
  if (!req.identity) return res.status(401).json({ error: 'Unauthenticated' });
  if (req.identity.role !== 'admin') {
    return res.status(403).json({ error: 'Forbidden' });
  }
  return next();
}

function register(app, users, authenticate) {
  app.delete('/users/:id', authenticate, adminOnly, (req, res, next) => {
    users.remove(req.params.id, (error) => {
      if (error) return next(error);
      return res.json({ deleted: true });
    });
  });
}
```

Injected authenticate verifies a signed expiring credential and loads the current
identity; roles from request input are never trusted. This example assumes an
approved admin-only deletion policy. Decide ownership separately for each resource.
Verify anonymous/ordinary user denial, invalid tokens and successful admin deletion
with persisted effects; denials alone do not establish functional preservation.

## AP-06 — Request-scoped connections

Before:

```python
import sqlite3

connection = sqlite3.connect("application.db", check_same_thread=False)

def get_db():
    return connection
```

After:

```python
import sqlite3
from flask import current_app, g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```

Call init_app from the application factory. Transaction owners explicitly commit
or roll back; teardown closes even on errors. Verify separate app contexts have
distinct connections and teardown closes each, including failing requests. Use a
disposable file: separate :memory: connections do not share schema. For a single
Node connection, serialize complete transactions, not just individual queries.

## AP-07 — Atomic business writes

Before:

```python
def enroll(connection, user_id, course_id, amount):
    enrollment = connection.execute(
        "INSERT INTO enrollments(user_id, course_id) VALUES (?, ?)",
        (user_id, course_id)).lastrowid
    connection.commit()
    connection.execute(
        "INSERT INTO payments(enrollment_id, amount) VALUES (?, ?)",
        (enrollment, amount))
    connection.commit()
    return enrollment
```

After:

```python
def enroll(connection, user_id, course_id, amount):
    with connection:
        enrollment = connection.execute(
            "INSERT INTO enrollments(user_id, course_id) VALUES (?, ?)",
            (user_id, course_id)).lastrowid
        connection.execute(
            "INSERT INTO payments(enrollment_id, amount) VALUES (?, ?)",
            (enrollment, amount))
    return enrollment
```

Use an idle connection with normal DB-API transaction behavior, not autocommit.
An exception rolls back both writes. The actual checkout's transaction must also
cover any new account and audit rows; validate the payment before writes when
possible. Verify induced payment failure leaves no enrollment/payment, successful
checkout persists both, and refusal leaves no new account or enrollment. Keep
external payment and email integrations simulated in tests.

## AP-08 — Set-based retrieval instead of N+1

Before:

```python
def enrollments(connection):
    result = []
    for row in connection.execute("SELECT id, user_id FROM enrollments"):
        user = connection.execute(
            "SELECT name FROM users WHERE id = ?", (row[1],)).fetchone()
        result.append({"id": row[0], "name": user[0] if user else None})
    return result
```

After:

```python
def enrollments(connection):
    rows = connection.execute(
        "SELECT e.id, u.name FROM enrollments e "
        "LEFT JOIN users u ON u.id = e.user_id ORDER BY e.id")
    return [{"id": row[0], "name": row[1]} for row in rows]
```

Left joins retain absent relationships. ORM eager loading/bulk queries may fit
other schemas. Verify empty/multiple rows and missing users. Measure SELECT count
with 1 and 20 enrollments (one in this example). Preserve contractual ordering and
avoid multiplying revenue by joining multiple one-to-many relations naively.

## AP-09 — Share validation rules

Before:

```python
def create_title(payload):
    title = payload["title"]
    if len(title) < 3 or len(title) > 200:
        raise ValueError("Invalid title")
    return title

def update_title(payload):
    title = payload["title"]
    if len(title) < 3:
        raise ValueError("Invalid title")
    return title
```

After:

```python
def validate_title(value):
    if not isinstance(value, str) or not 3 <= len(value) <= 200:
        raise ValueError("Invalid title")
    return value

def create_title(payload):
    return validate_title(payload.get("title"))

def update_title(payload):
    return validate_title(payload["title"]) if "title" in payload else None
```

None on update means no change; preserve that distinction in the controller.
Approve stricter update validation in the contract diff. Verify lengths 2/3/200/201,
nonstring input, missing create input and omitted update input. Shared serializers
likewise must retain fields specific to list/detail response contracts.

## AP-10 — Version-compatible replacement of deprecated APIs

Before:

```python
from datetime import datetime

def find_user(session, user_model, user_id):
    return session.query(user_model).get(user_id)

def now_for_legacy_storage():
    return datetime.utcnow()
```

After:

```python
from datetime import datetime, timezone

def find_user(session, user_model, user_id):
    return session.get(user_model, user_id)

def now_for_legacy_storage():
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

Query.get is legacy in SQLAlchemy 2.x; datetime.utcnow is deprecated from Python
3.12. Confirm runtime versions before classifying. Removing timezone here applies
only to a confirmed naive-UTC legacy storage/HTTP contract. Use aware UTC end to
end when that is the actual contract; normalize at one boundary to prevent mixed
datetime comparisons. Verify existing/missing IDs, legacy dates, date boundaries
and unchanged response format with deprecation warnings enabled. Sources:
[SQLAlchemy Query.get](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html#sqlalchemy.orm.Query.get),
[Python datetime.utcnow](https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow).

## AP-11 — Named domain thresholds

Before:

```python
def discount(revenue):
    if revenue > 10000:
        return revenue * 0.1
    if revenue > 5000:
        return revenue * 0.05
    if revenue > 1000:
        return revenue * 0.02
    return 0
```

After:

```python
DISCOUNT_TIERS = ((10000, 0.1), (5000, 0.05), (1000, 0.02))

def discount(revenue):
    for threshold, rate in DISCOUNT_TIERS:
        if revenue > threshold:
            return revenue * rate
    return 0
```

Descending order and strict comparison preserve the existing policy. Keep rounding
at the original boundary. Verify below/equal/above each threshold and zero; naming
constants does not authorize changing business values.

## AP-12 — Clear internals and proven dead code removal

Before:

```javascript
const { totalRevenue } = require('./utils');

function checkoutInput(body) {
  const u = body.usr;
  const cid = body.c_id;
  return { name: u, courseId: cid };
}
```

After:

```javascript
function checkoutInput(body) {
  const userName = body.usr;
  const courseId = body.c_id;
  return { name: userName, courseId };
}
```

Public keys usr/c_id remain unchanged. Inspect module initialization for intentional
side effects before removing a require; search callers before removing an export
or declaration. Verify mapping and boot, and run the existing linter if available.
Naming alone does not justify rewriting a correct public API.
