# Runtime e APIs — verificação posterior à aprovação

Python 3.12.10 e SQLAlchemy 2.1.6 foram medidos no ambiente novo, por sys/importlib.metadata sem importar aplicação; não foram inferidos do requirements. Arquivo runtime.json registra versões exatas. O launcher py instalado apontava para Python 3.14 ausente; utilizou-se python.exe Python312 e ambiente novo.

Fontes oficiais consultadas em 2026-10-23:
- https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow — deprecia utcnow desde Python 3.12; usar now com UTC. Código usa utils.domain.utcnow com now(timezone.utc) e remove tzinfo somente para manter contrato UTC ingênuo existente.
- https://docs.sqlalchemy.org/en/21/orm/queryguide/query.html#sqlalchemy.orm.Query.get — Query.get é legacy/deprecated em SQLAlchemy 2.x; usar Session.get. models.store.get usa db.session.get e consultas com select.

As suspeitas AP-10 originais foram confirmadas depois de estabelecer runtime, sem alterar retroativamente a contagem dos 13 achados aprovada. As substituições são compatibilidade das consultas/regras já transformadas em T05/T10; não adicionam diferença funcional nem um novo escopo. MD5 foi classificado como armazenamento de senha fraco, não API deprecated.
