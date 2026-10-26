# Auditoria aprovada — Task Manager API

Data: 2026-10-23. Árvore limpa na análise e na reverificação anterior a qualquer edição. [Skill local](../task-manager-api/.agents/skills/refactor-arch/SKILL.md), SHA256 `5113639E569AE7CB391CCD924971C31A9B06F9F3994D3A9724B4F9E4E8BDB937`. Aprovação humana recebida depois da apresentação das Fases 1/2: **“Aprovo o escopo completo apresentado”**, 2026-10-23. Escopo: T01–T13, matriz, diferenças, migração e rollback abaixo.

## Fase 1

15 fontes Python originais, incluindo cinco __init__.py e seed.py. Excluídos testes existentes, ambientes, caches, dados locais e outros projetos. Nenhum aplicativo importado, banco acessado ou relatório escrito durante Fases 1/2. As referências locais da skill foram lidas.

Python/Flask. Declarados: Flask 3.0.0, Flask-SQLAlchemy 3.1.1, Flask-CORS 4.0.0, Marshmallow 3.20.1, Requests 2.31.0, python-dotenv 1.0.0; runtime e dependências instaladas não verificados na auditoria. SHA256 requirements original: C56CBF059924E9A56AE63017CAC7861DED0CFBDEE88792D59D0B8F99BD789F00. SQLite tasks.db com ORM users/tasks/categories. app.py registra blueprints e cria schema na importação; seed.py importa app e apaga dados quando executado. MVC parcial: Models úteis; Controllers sem fontes; Routes contêm HTTP, consultas, negócio, serialização e commits. NotificationService não tem consumidor HTTP.

## Fase 2

13 confirmados: **CRITICAL 2 | HIGH 5 | MEDIUM 4 | LOW 2**. Linhas a seguir referem-se à revisão original. Rubric classifica exposição de hashes/credenciais operacionais como CRITICAL; MD5 fraco não significa API deprecated.

| ID / severidade / catálogo | Evidência exata original e impacto | Correção / verificação / dependências / contrato |
|---|---|---|
| T01 CRITICAL AP-02 | models/user.py:16–25 (21); routes/user_routes.py:33–40,85–86,128–129,207–211. Hash MD5 em GET detalhe/criação/alteração/login facilita quebra offline. | Serializer público remove password. Verificar ausência recursiva com sentinelas e demais campos. Sem dependência obrigatória; T04 protege armazenamento. Diferença: remove password. |
| T02 CRITICAL AP-02 | app.py:11–15; services/notification_service.py:7–19. Chave fixa e credencial entregue a SMTP.login; validade externa não verificada e serviço não ligado às rotas. | Config externa e rotação se implantada. Verificar configuração ausente/presente, logs e SMTP simulado. T04 depende de configuração segura. Diferença operacional de configuração. Seed ilustrativo não contado como segredo de produção. |
| T03 HIGH AP-05 | app.py:18–20; routes/task_routes.py:11–299; user_routes.py:10–183,52,71–78,119–125; report_routes.py:12–223. Acesso anônimo, tomada de conta e promoção livre. | Identidade assinada, conta ativa/papel atuais e propriedade. Testar matriz com sucesso persistido e negativas. Depende T04/T02. Diferenças 401/403, campos e recortes abaixo. |
| T04 HIGH AP-04 | models/user.py:27–32; routes/user_routes.py:197–211. MD5 rápido sem salt e token previsível sem expiração/verificação. | Hash moderno, token assinado expirável, upgrade MD5 em janela explícita. Testar Unicode, senha errada, salt, upgrade persistido, expiração/adulteração/inatividade. Depende T02; implantação coordenada T03. Token antigo inválido. |
| T05 HIGH AP-03 | routes/task_routes.py:85–223; user_routes.py:42–151; report_routes.py:12–155,167–223. Routes acoplam HTTP, banco e domínio. | Routes finas, Controllers e persistência explícita; serviços só com orquestração relevante. Rastrear domínios e regressão 22 contratos. Sem dependência; preservar contratos exceto diferenças aprovadas. |
| T06 HIGH | app.py:33–34. Execução direta debug=True em 0.0.0.0, risco operacional do debugger; ambiente externo desconhecido. | Config/default seguro; testar boot e perfil debug. Config pode compartilhar T02. Diferença só inicialização/debug. |
| T07 HIGH AP-07 | seed.py:8–14,16–37,39–63,78–92,98–99. Exclusão confirmada antes de reconstrução; falhas deixam base parcial/vazia. | Destino descartável/aceite explícito e transação única; falhar em cada etapa e comprovar rollback. Depende T11. Diferença CLI e operação de seed, dados ilustrativos preservados. |
| T08 MEDIUM AP-09 | task_routes.py:87–114,140–144,162–184,209–213,240–264; user_routes.py:44–65,98–125,187–201; report_routes.py:169–180,196–202. len/comparação/join/int com tipos inválidos causam 500; bool pode virar prioridade. | Validar objeto/tipos/limites antes de mutação; testar omitido/null/vazio, bool, tags, datas, filtros e persistência intacta. Sem dependência; compartilhar T10. Diferença inválidos→400; não inventar políticas extras de cor/email/tamanho. |
| T09 MEDIUM AP-08 | task_routes.py:14–57; user_routes.py:12–22; report_routes.py:53–68,159–164,15–30. Consultas por entidade e agregação carregando registros. | Eager loading/agregações sem multiplicação. Medir 1/20 entidades, relações ausentes, base vazia e resultados. Sem dependência. Contrato preservado, sem paginação nova. |
| T10 MEDIUM AP-09 | models/task.py:23–36,50–60; task_routes.py:17–39,71–80,283–287; user_routes.py:162–180; report_routes.py:33–43,132–135; utils/helpers.py:57–108. Regras/serialização duplicadas; helper não é equivalente (trim, coerção, outro formato data). | Regras compartilhadas, serializers específicos por resposta; relógio controlado e chaves/mensagens/formato preservados. Coordenar T08; não substituir pelo helper integralmente. Contrato preservado. |
| T11 MEDIUM | app.py:9–16,30–31; seed.py:2. Importar cria schema/banco e configura destino fixo. | Factory/config e init-db explícito; importar sem arquivo/schema e boot após init. T07 usa nova inicialização. Diferença setup, HTTP preservado. |
| T12 LOW AP-11 | task_routes.py:96–114,166–184; user_routes.py:64–72,115–121; models/task.py:38–47; utils/helpers.py:110–116 sem consumo. Valores repetidos. | Constantes únicas, sem alterar valores/mensagens; testar fronteiras. Coordenar T10. Senha mínima continua 4. Contrato preservado. |
| T13 LOW AP-12 | app.py:7 os/sys/json; task_routes.py:7; user_routes.py:6 hashlib/json; report_routes.py:7–8; models/task.py:3; utils/helpers.py:3–7. Imports mortos; report_routes.py:24–28 p1..p5 e category.py:14–21 d. | Remover imports comprovados, nomes internos claros; referências e boot. Sem dependência. Não remover API/export só por ausência de chamada interna. Contrato preservado. |

Suspeitas não contadas: Query.get legacy (SQLAlchemy efetivo não consultado); datetime.utcnow deprecated a partir Python 3.12 (runtime não consultado). NotificationService tem lista mutável mas nenhuma ligação HTTP; não declarar estado global inseguro nas requisições. ORM db extension não equivale conexão SQLite global. LIKE ORM não prova SQL injection. CRUD HTTP tem commit único/rollback; falha transacional confirmada é do seed.

## Inventário HTTP — 22 pares

Task = models/task.py:23–36; User = models/user.py:16–25 (password incluído originalmente); Category = models/category.py:13–21. HEAD/OPTIONS automáticos excluídos. Status representam fonte, não runtime verificado na auditoria.

| Método/caminho | Fonte original | Entrada/sucesso/erros explícitos |
|---|---|---|
| GET / | app.py:26–28 | 200 message/version |
| GET /health | app.py:22–24 | 200 status/timestamp |
| GET /users | user_routes.py:10–25 | 200 lista sem password + task_count |
| GET /users/<int:user_id> | :27–40 | 200 User + tasks Task;404 |
| POST /users | :42–90 | name,email,password,role?;201 User;400/409/500 |
| PUT /users/<int:user_id> | :92–132 | name/email/password/role/active opcionais;200 User;400/404/409/500 |
| DELETE /users/<int:user_id> | :134–151 | 200 message; exclui tarefas;404/500 |
| GET /users/<int:user_id>/tasks | :153–183 | 200 id/title/description/status/priority/created_at/due_date/overdue;404 |
| POST /login | :185–211 | email/password;200 message/user/token;400/401/403 |
| GET /tasks | task_routes.py:11–63 | 200 Task + overdue/user_name/category_name;500 |
| GET /tasks/<int:task_id> | :65–83 | 200 Task + overdue;404 |
| POST /tasks | :85–154 | title, description/status/priority/user_id/category_id/due_date/tags?;201 Task;400/404/500 |
| PUT /tasks/<int:task_id> | :156–223 | campos opcionais;200 Task;400/404/500 |
| DELETE /tasks/<int:task_id> | :225–238 | 200 message;404/500 |
| GET /tasks/search | :240–271 | q/status/priority/user_id;200 Task[] |
| GET /tasks/stats | :273–299 | 200 total/pending/in_progress/done/cancelled/overdue/completion_rate |
| GET /reports/summary | report_routes.py:12–101 | 200 generated_at/overview/tasks_by_status/tasks_by_priority/overdue/recent_activity/user_productivity |
| GET /reports/user/<int:user_id> | :103–155 | 200 user(id/name/email),statistics;404 |
| GET /categories | :157–165 | 200 Category[] + task_count |
| POST /categories | :167–188 | name,description/color?;201 Category;400/500 |
| PUT /categories/<int:cat_id> | :190–209 | name/description/color?;200 Category;404/500 |
| DELETE /categories/<int:cat_id> | :211–223 | 200 message;404/500 |

## Matriz aprovada

Antes: todos os pares públicos; login verifica senha/status apenas no próprio fluxo. Depois: conta/papel atual carregados após token válido. Ausente/inválido/expirado=401; conta inativa login=403 e não autoriza outras chamadas; permissão negada=403. Recursos inexistentes preservam 404 quando autorizado.

| Operação | Anônimo | User ativo | Manager ativo | Admin ativo |
|---|---|---|---|---|
| GET /, GET /health, POST /login | sim | sim | sim | sim |
| POST /users | somente role=user | cadastro público user | cadastro público user | pode definir papel |
| GET /users |401|403|todos|todos|
| GET usuário/tarefas do usuário/relatório do usuário |401|próprio|qualquer|qualquer|
| PUT usuário |401|próprio name/email/password|próprio name/email/password|qualquer; role/active exclusivos|
| DELETE usuário |401|403|403|sim, exclui tarefas|
| listar/buscar/GET tarefas |401|próprias|todas|todas|
| POST tarefa |401|própria; omitido assume identidade; outro/null recusado|atribuição livre válida|atribuição livre válida|
| PUT/DELETE tarefa |401|própria, sem transferência|qualquer|qualquer|
| stats tarefas |401|próprias|globais|globais|
| relatório global |401|403|sim|sim|
| GET categorias |401|sim|sim|sim|
| POST/PUT/DELETE categoria |401|403|sim|sim|

Tarefa sem proprietário é acessível só manager/admin. Nenhuma rota nova.

## Diferenças aprovadas e verificações

1. GET detalhe/POST/PUT usuário e login removem password; demais chaves preservadas (sentinelas recursivas).
2. Login emite token assinado expirável; tokens falsos antigos inválidos (adulteração, clock, inatividade).
3. Todos os pares protegidos exigem credencial/papel/propriedade da matriz, com 401/403 e sucesso persistido.
4. Listagens/busca/stats/relatórios usam recorte aprovado; usuário comum não cadastra papel privilegiado nem altera role/active.
5. Criação comum de tarefa sem user_id assume identidade; null/outro dono recusados; transferência recusada ao user.
6. Entradas de tipos inválidos antes aceitas/500 passam a 400. Omitido/null/vazio legítimos, mensagens específicas e limites atuais preservados; não aumentar mínimo senha nem impor nova política de cor/email.
7. Importação não cria schema; setup exige init explícito; configuração externa/debug seguro/seed controlado.
8. MVC, agregação, serializers, constantes e imports preservam contratos. Preservar SQL LIKE (%/_/Unicode/case), diferenças de chaves por endpoint, datas UTC ingênuas/strings existentes, zero/base vazia e efeitos de exclusão de usuário.

## Plano, dependências, migração e rollback

Após recheck/gravação desta aprovação: baseline original isolado, testes RED, factory/config/init (T11/T02/T06), MVC incremental (T05), segurança coordenada (T01/T04/T03), validação/regras (T08/T10/T12), consultas (T09), limpeza (T13), seed (T07), HTTP real/revisão final. Cada correção permanece nesta execução com evidência e regressão; não usar implementações antigas. T03 depende T04/T02; T07 depende T11; T10/T12 compartilham regras. Escopo parcial nunca implica dependências; aqui todos aprovados.

Usar somente bancos descartáveis durante validação. Nunca apagar/reseed base real; backup antes de migração autorizada. Schema/IDs/relações/datas/tags preservados. Hash MD5 reconhecido pode fazer upgrade só após login válido dentro de janela com cutoff configurável; após corte exigir reset. Nunca fallback MD5 depois de falha de hash moderno. Testar os dois lados do corte com relógio controlado. Rotacionar segredos se implantados e invalidar token antigo. Não descartar registros inconsistentes silenciosamente.

Rollback por checkpoints de código/config/banco. Após upgrade, código MD5 antigo não lê hash moderno: rollback requer manter verificador moderno compatível ou restauração controlada de backup com avaliação de perdas. Nunca converter hash moderno em MD5 nem restaurar segredo rotacionado. Reverter autorização reabre exposição e exige decisão operacional explícita. Falha de validação mantém entrega incompleta; boot/sucesso autorizado/cleanup são obrigatórios.

Gate apresentado na conversa: “Você aprova esta auditoria, a matriz de acesso, todas as diferenças contratuais e o plano de migração/rollback, ou seleciona apenas os IDs que deseja executar?” Resposta efetiva registrada acima. Relatório criado apenas após essa aprovação e antes de editar aplicação.
