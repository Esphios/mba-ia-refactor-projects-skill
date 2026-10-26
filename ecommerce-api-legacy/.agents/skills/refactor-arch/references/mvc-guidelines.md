# Adaptable MVC boundaries

MVC is accepted only when all three responsibilities are explicit and testable.

| Boundary | Owns | Must not own |
| --- | --- | --- |
| View/Route | HTTP method/path, request adaptation, response/status | SQL, multi-step business rules |
| Controller | use-case coordination and application decisions | framework startup, raw persistence details |
| Model | entity rules and persistence abstraction | request/response objects |

Configuration, error mapping, authentication middleware and composition are separate
supporting concerns. A service is useful for a transaction spanning models, an
external integration, or reusable domain orchestration. Do not add a pass-through
service merely to imitate a preferred folder tree.

## Adaptation examples

- Direct SQLite: introduce an explicit connection lifecycle and repositories/models;
  keep transaction ownership at the use-case boundary.
- ORM: retain useful entity mappings, move queries and coordination out of routes,
  and make session/transaction boundaries visible.
- Express: export a testable app separately from startup; await database readiness
  before listening; centralize error middleware.
- Partially organized Flask: preserve useful blueprints/models/services and move
  only responsibilities proven to be misplaced.

Trace at least one request per domain from route through controller to model and
back. Reject circular imports, models importing HTTP objects, SQL in routes, and
controllers that merely rename a monolithic handler without separating concerns.
