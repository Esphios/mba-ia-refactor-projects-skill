# Evidence-based project analysis

## Inspection order

1. Read repository instructions and record Git revision/status.
2. Locate manifests, lockfiles, entry points and configuration.
3. Enumerate source files, excluding dependencies, virtual environments, caches,
   generated output and local data.
4. Trace route registration to controller/handler, persistence and integrations.
5. Inventory each explicit method/path; do not count automatic HEAD/OPTIONS.
6. Check every catalog family against evidence, including imports/exports that can
   be proven unused by repository-wide search; do not stop after reaching a count.
7. Separate declared versions from versions verified by a non-mutating runtime query.

Do not install packages or execute application imports during read-only phases when
an import can initialize schema, seed data or start a service.

## Stack-specific evidence

| Shape | Evidence to seek | Do not assume |
| --- | --- | --- |
| Flask + direct SQLite | `app.py`, `add_url_rule`, decorators, connection lifecycle, SQL sites | `models.py` is a Model layer or global connection is safe |
| Flask + ORM | app factory, extensions, blueprints, model queries, session boundaries | blueprints imply thin routes or ORM prevents N+1 |
| Express + SQLite | `package.json`, lockfile, app/startup split, router registration, callback/Promise DB API | class names imply controller boundaries or schema initialization is awaited |
| Partially organized project | imports and complete request-to-data traces | directories named models/routes/services satisfy MVC |

For an unknown stack, report discovered files and missing facts. Ask for the entry
point or supported run command rather than generating Flask/Express scaffolding.

## Required Phase 1 output

- project root, revision and dirty paths;
- language, framework and versions (`declared`, `verified`, or `unverified`);
- dependency and persistence summary;
- domain and entry points;
- current responsibility map and coupling;
- endpoint count and inventory source;
- analyzed source-file count plus explicit exclusions;
- uncertainties and read-only constraints observed.
