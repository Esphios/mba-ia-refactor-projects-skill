# Auditoria — Task Manager API

Data: 2026-10-22. Revisão original: `6d1ce6248c3e956801010a89d8bdaab48029bf30`. Fontes do projeto sem alterações antes desta auditoria; mudanças de outros projetos existem no workspace. Escopo: 15 arquivos Python originais (excluídos ambientes e caches; snapshot em evidence/project-3-original-sources.json). Python 3.12.10 verificado; Flask 3.0.0 / Flask-SQLAlchemy 3.1.1 declarados, instalados registrados no baseline. SQLite, domínio de tarefas/usuários/categorias, app.py com inicialização de schema por importação. Blueprints existentes concentram HTTP, regras e consultas; models úteis preservados. 22 pares método/caminho no inventário reports/planning/contracts.md.

Autorização excepcional do usuário: **“ignore as aprovações por enquanto. continue até o fim.”**. Este waiver substitui as pausas da skill somente nesta execução. Auditoria salva antes das alterações de fontes; revisão conferida. Não representa teste independente de aprovação. Pacote copiado integralmente da versão canônica; hashes serão conferidos na validação.

## Achados confirmados

| ID | Severidade / catálogo | Evidência original (linhas) | Impacto / correção / verificação |
|---|---|---|---|
| P3-01 | CRITICAL AP-02 | models/user.py:15–25 retorna password em to_dict, routes/user_routes.py usa o resultado em GET/POST/PUT/login | Hash exposto facilita ataque offline; whitelist compartilhada, testes em todas respostas de usuário |
| P3-08 | CRITICAL AP-02 | services/notification_service.py:8–11 SMTP/senha fixos | Credenciais hardcoded são CRITICAL segundo a rubrica do desafio; configuração externa e transporte injetável sem envio em testes |
| P3-06 | HIGH AP-04 | models/user.py:27–32 MD5 sem salt | Quebra rápida; scrypt para novas senhas e upgrade transacional após login legado válido com cutoff configurável |
| P3-07 | HIGH AP-05/AP-04 | routes/user_routes.py:1–230 sem autorização, token fake-jwt-token; app.py:14 segredo fixo | Escalada e alteração de terceiros; token assinado expirável, identidade atual ativa e matriz owner/admin |
| P3-02 | MEDIUM AP-08 | routes/task_routes.py:15–57 consulta usuário/categoria por tarefa; routes/report_routes.py:55–58,161–163 consultas por usuário/categoria | Crescimento N+1; joined/selectin loading e contagem comparativa 1/20 |
| P3-03 | MEDIUM AP-09 | routes/task_routes.py:17–59,69–82,96–139,165–212; utils/helpers.py:62–116 | Validação e overdue/serialização duplicados; funções únicas com preservação dos campos por contexto |
| P3-09 | MEDIUM AP-10 | routes/task_routes.py:42,51,67 e models/task.py:17–18,66 | Query.get legacy em SQLAlchemy 2; utcnow deprecated Python 3.12. Fontes oficiais https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html#sqlalchemy.orm.Query.get e https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow ; Session.get e UTC normalizado para persistência ingênua legada |
| P3-04 | LOW AP-12 | utils/helpers.py:3–7; routes/task_routes.py:7 | imports os/json/sys/math/hashlib/time sem referências; remover e validar boot |
| P3-05 | LOW AP-11 | routes/report_routes.py:24–28,129; routes/task_routes.py:104,113 | Prioridades sem nomes compartilhados; constantes 1–5/default 3 mantendo política |

Resumo: 2 CRITICAL, 2 HIGH, 3 MEDIUM, 2 LOW. Nenhuma suspeita contada.

Conferência editorial de 23/10/2026: P3-08 foi reclassificado de HIGH para CRITICAL para cumprir a rubrica explícita de credenciais hardcoded. A tabela foi reordenada e o resumo recalculado; evidências, escopo, autorização original e correções permanecem os mesmos. Este registro não apresenta a reclassificação como saída bruta original.

## Transformações e diferenças de contrato

Escopo completo dos achados acima autorizado pelo waiver. Dependências: retirada de hash e MD5 exigem login/migração; autorização exige token verificável e configuração; serializers/eager loading dependem da extração das regras. Ordem: baseline descartável, testes RED, config/factory/errors, modelos/repositório/controllers/rotas, segurança, regressão/boot. Rollback: restaurar fontes e backup SQLite anterior; não reverter hash scrypt para MD5. Não executar seed em dados existentes.

Inventário integral dos 22 contratos e fixtures: reports/planning/contracts.md, seção Projeto 3 (incorporado por referência). Todos os métodos/caminhos e campos legítimos de sucesso serão mantidos. Diferenças deliberadas:

- Todas as respostas de usuário removem password/hash (incluindo login e detalhes); token falso substituído por assinado com expiração.
- Tarefas/lista/search/stats e usuários individuais/tarefas/relatório: titular ou admin; lista users e resumo: admin; categorias lista autenticada e escrita admin. Não autenticado 401, terceiros 403, conta inativa sem acesso.
- POST users público aceita somente role user; PUT role e active exige admin; tentativas de promoção por titular recebem 403.
- Criação de tarefa associa identidade autenticada por padrão; atribuição a terceiro exige admin. Referências inexistentes 404 e corpo/tipos/datas/prioridade malformados 400, sem alterações parciais.
- Novas senhas scrypt; hashes MD5 reconhecidos explicitamente apenas antes de LEGACY_MD5_CUTOFF e atualizados somente após login correto de conta ativa; após cutoff requer redefinição administrativa. Nenhuma limpeza/migração destrutiva no startup.
- SMTP desabilitado por padrão, configuração ambiental, transporte substituído nos testes; sem envio externo.
- Exclusão de usuário mantém remoção transacional de suas tarefas; exclusão de categoria mantém desvinculação das tarefas (category_id null), preservando o comportamento ORM original.
- Saúde consulta banco e sanitiza falhas 503; erros internos não retornam detalhes ou segredos. Configuração exige segredo externo em produção.

Consultas parametrizadas do ORM não são injeção SQL; scoped session existente não é conexão global insegura. Não adicionar falsos positivos por nomes de pasta.

## Evidências executadas antes da implementação

[Baseline original descartável](evidence/project-3-baseline.log), [testes RED](evidence/project-3-red.log) e [snapshot original com segredos explicitamente redigidos](evidence/project-3-original-sources.json). A contagem do baseline é 20 pares de blueprints mais GET / e GET /health = 22. O teste RED de factory importou app original, criando somente arquivo SQLite local gerado pelo import legado; nenhum banco pré-existente foi utilizado e o arquivo gerado está excluído da entrega.

Versões verificadas no ambiente próprio: Python 3.12.10, Flask 3.0.0, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.6, Werkzeug 3.1.9, itsdangerous 2.2.0. Fonte da versão aplicável: [SQLAlchemy 2.1 Query.get](https://docs.sqlalchemy.org/en/21/orm/queryguide/query.html#sqlalchemy.orm.Query.get) e [Python 3.12 utcnow](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow), consultadas em 2026-10-22.

CORS: o CORS global permissivo foi removido; a aplicação aceita mesma origem por padrão. Integrações browser entre origens precisam política explícita no proxy/configuração de implantação. Este endurecimento faz parte do escopo de segurança autorizado pelo waiver.
