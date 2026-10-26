# Auditoria aprovada — ecommerce-api-legacy

Data: 2026-10-23. Execução real da [skill local](../ecommerce-api-legacy/.agents/skills/refactor-arch/SKILL.md), Fases 1/2 por inspeção estática, seguida de autorização para Fase 3.

## Aprovação e estado anterior às alterações

Resposta humana transmitida pelo coordenador: **“Aprovo o escopo completo apresentado”**, em **2026-10-23**. Escopo: E01–E13 e todas as diferenças abaixo; Basic auth, verificação de senha no checkout existente, exclusão física sem vínculos e desativação com vínculos, retenção financeira, nenhum novo endpoint. Não houve implementação antes desta aprovação.

Revisão auditada e reverificada imediatamente antes deste arquivo, com árvore de trabalho limpa no preflight. Outros projetos foram tratados em execuções isoladas. Os resultados e o inventário das evidências estão na [validação do projeto 2](validation-project-2.md).

SHA-256 anterior às alterações:

| Arquivo | Hash |
|---|---|
| `.agents/skills/refactor-arch/SKILL.md` | `5113639E569AE7CB391CCD924971C31A9B06F9F3994D3A9724B4F9E4E8BDB937` |
| `package.json` | `58A14B9AB83C508A285ABBCC1787D64090534502BBF2D3EDA12053EB24E78D90` |
| `package-lock.json` | `82AC34E44F3A7C82893CDB99715FA851E3D66F6342FBB15C406A2A20C20C303A` |
| `src/app.js` | `BF2C87F0AD5604772058C5A9CB758841D2DF5C314B7B644BBF4A3C8C75474FC3` |
| `src/AppManager.js` | `5906937CFD56420A25B42ABCEAD09F520BBF133030C7B1F816B0B374501CEA36` |
| `src/utils.js` | `0739B7FACD3BDEE5CB0E70C0E8FC00B220A2D9151C0CEF9512D1A26D994A4390` |

## Fase 1 — análise

Alvo: `ecommerce-api-legacy/`, LMS com usuários, cursos, matrículas, pagamentos e auditoria. Três fontes JavaScript analisadas integralmente: `src/app.js`, `src/AppManager.js`, `src/utils.js`. Também foram analisados manifests/lockfile, README local e api.http. Referências da skill: project-analysis, anti-patterns, audit-report-template, mvc-guidelines, refactoring-playbook, delivery e regression-checks. Excluídos node_modules, caches, outros projetos e backups.

JavaScript CommonJS/Node, Express declarado ^4.18.2, sqlite3 ^5.1.6; lockfile registra Express 4.22.1 e sqlite3 5.1.7. Runtime e módulos não executados nas Fases 1/2. Na continuação autorizada, preflight mediu Node v24.12.0 e npm 11.19.1; versões carregadas serão verificadas após npm ci. SQLite :memory:, uma conexão por AppManager; schema e seeds automáticos. Entrada npm start → node src/app.js; porta 3000. Sem limites MVC reais: AppManager combina schema, seed, conexão, HTTP, regras e SQL; utils combina configuração, senha, log e cache. Não há transações, FKs ou unicidade de email. Pagamento é simulação por prefixo, sem integração externa.

## Inventário original — 3 métodos/caminhos

Não inclui HEAD/OPTIONS automáticos.

| Método/caminho | Entradas/comportamento | Respostas/efeitos |
|---|---|---|
| POST /api/checkout | JSON usr, eml, pwd, c_id, card; apenas truthiness de usr/eml/c_id/card. Curso ativo; email existente não verifica senha. Novo usuário usa badCrypto(pwd ou senha padrão). Aceita cartão cujo startsWith('4') é verdadeiro. | 400 Bad Request; 404 Curso não encontrado (inclusive erro DB do curso); 500 Erro DB; 500 Erro ao criar usuário; 400 Pagamento recusado; 500 Erro Matrícula; 500 Erro Pagamento; 200 {msg:'Sucesso',enrollment_id:number}. Cria conta antes da recusa, matrícula/pagamento/auditoria separados; erro auditoria ignorado. |
| GET /api/admin/financial-report | Público. Todos os cursos, inclusive inativos, matrículas, usuário e um pagamento por matrícula. | 500 Erro DB na consulta inicial; 200 [{course,revenue,students:[{student,paid}]}]. Curso vazio: 0/[]. Usuário ausente: Unknown; pagamento ausente: paid 0. paid inclui amount mesmo não PAID; revenue soma somente PAID. Sem ORDER BY. |
| DELETE /api/users/:id | Público. ID parametrizado. | 200 texto 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.', inclusive inexistência ou erro. Apaga somente usuário, deixando vínculos órfãos. |

## Achados confirmados

**13 achados: 2 CRITICAL, 5 HIGH, 3 MEDIUM e 3 LOW.** Referências abaixo relativas ao alvo e às linhas originais desta revisão. Cada verificação é compromisso de Fase 3, não alegação de teste já executado.

### E01 — AP-02 — CRITICAL — exposição sensível

Evidência: AppManager.js:18 senha seed literal; :45 cartão completo/chave em log; utils.js:1–7 configuração apresentada como credenciais. Impacto: cartão efetivamente recebido é exposto a logs, senha da conta seed está em fonte. Não há prova de credencial externa válida: dbPass não é utilizado pelo SQLite e chave só é logada. Correção: remover dados sensíveis dos logs, credenciais e seed inseguro do boot normal. Verificação: logs com sentinelas, respostas sem senha/hash. Dependência E03 para credenciais seguras. Contrato HTTP preservado; bootstrap/logs mudam.

### E02 — AP-03 — CRITICAL — God Class

Evidência: AppManager.js:4–139, especialmente :7–22/:28–78/:80–129/:131–137 contém DB/DDL/seed/HTTP/regras. Impacto: separação de responsabilidades integralmente violada. Correção: MVC e composição injetável, serviço somente para orquestração real. Verificação: fluxos HTTP por domínio, SQL só em models/infra, módulos sem HTTP em persistência. Dependências: coordena achados aprovados; extração pura não autoriza mudanças adicionais. Contrato preservado na extração.

### E03 — AP-04 — HIGH — senha parcial e padrão

Evidência: utils.js:17–22 repete dois caracteres Base64 e trunca em dez; AppManager.js:68–69 usa senha padrão quando ausente. Impacto: colisões, derivação parcial não verifica senha completa. Correção: hash com salt/custo suportado pelo runtime, sem padrão; reset confiável obrigatório para truncados, sem fallback. Verificação: Unicode, prefixos iguais/senhas diferentes, errada, salt, persistência. Dependência E04/bootstrap/reset. Contrato: senha obrigatória em cadastro; legado truncado não autentica automaticamente.

### E04 — AP-05 — HIGH — autenticação/autorização ausentes

Evidência: AppManager.js:40–41/:66–75 email existente basta para matrícula; :80 relatório público; :131–135 exclusão arbitrária; app.js:5–10 não autentica. Impacto: ações em nome alheio e relatório nominal exposto. Correção: política Basic/current-user/ownership abaixo. Verificação: anônimo/titular/terceiro/admin, sucesso real além de 401/403. Dependências E03/E07/E02. Contrato muda explicitamente conforme tabela.

### E05 — AP-07 — HIGH — escritas parciais no checkout

Evidência: AppManager.js:66–72 cria conta antes da recusa :45–48; matrícula :50–52, pagamento :54–55, auditoria :57–60 são independentes. Impacto: resíduos/financeiro inconsistente. Correção: simular antes de escrever, lookup/decisão/conta/matrícula/pagamento/auditoria/commit na unidade transacional; rollback integral. Verificação: recusa, falha em cada escrita/auditoria/commit e concorrência. Dependências E06/E09. Contrato: recusa/falha sem resíduos; auditoria falha deixa de retornar 200.

### E06 — AP-06 — HIGH — ciclo de vida/sequenciamento implícitos

Evidência: AppManager.js:7–22 inicia sem resultado aguardável ou tratamento abertura/DDL/seed; app.js:8–12 ouve sem await. Sem fechamento. Impacto: readiness não prova schema pronto, erros de inicialização não coordenados. Correção: inicializar antes de listen, shutdown explícito, fila da unidade inteira em conexão única. Verificação: falha abertura/schema/readiness, transações concorrentes e fechamento. Dependência E02; requisito E05/E07. Contrato: startup falho não anuncia pronto. serialize atual enfileira comandos de inicialização, mas não é transação ou Promise, nem prova exclusividade de futuros callbacks. Não se afirma que toda consulta ultrapassa DDL.

### E07 — AP-07/AP-05 — HIGH — exclusão sem retenção/integridade

Evidência: AppManager.js:14–15 sem relações declaradas; :131–135 apaga só usuário; :112–114 admite Unknown. Impacto: vínculo financeiro órfão. Correção aprovada: desativar com vínculo, preservar dados/histórico; remover fisicamente sem vínculo; decisão e escrita sob exclusividade transacional. Verificação: proprietário/admin, histórico/receita preservados, conta inativa bloqueada, concorrência. Dependências E04/E06/E09. Contrato: DELETE funcional pode desativar, texto muda; sem cascata ou anonimização automática.

### E08 — AP-08 — MEDIUM — N+1 financeiro

Evidência: AppManager.js:83–106: 1 + C + 2E consultas no caminho completo. Impacto: custo cresce com matrículas. Correção: leitura em conjunto/número limitado de consultas. Verificação: 1/20 matrículas, vazios/inativos, usuário/pagamento ausentes, não PAID, multiplicidade histórica, contagem SELECT. Dependências E02/E09, observar E07. Contrato preserva formato, zeros, Unknown, paid, soma só PAID e ausência de ordenação contratada; não multiplicar receita em JOIN.

### E09 — erros — MEDIUM — callbacks ignorados

Evidência: AppManager.js:37–38 converte erro DB em 404; :57–60 ignora erro auditoria; :92–93 acessa length sem verificar erro; :104–106 ignora erros; :133–135 declara exclusão em falha. Impacto: sucesso falso/crash/HTTP inconclusivo. Correção: SQLite aguardável e mapper HTTP central. Verificação: falhas em consultas/escritas e uma resposta por request. Dependências E02/E05/E07. Contrato: erros técnicos 500 controlado, preservando mensagens legítimas existentes.

### E10 — validação — MEDIUM

Evidência: AppManager.js:29–35 truthiness apenas; :46 startsWith sem tipo; :68 senha omitida; :132–133 ID não validado. Impacto: entrada incompatível pode lançar em callback assíncrono. Correção: corpo objeto, tipos, IDs positivos, card string, nome/email/senha não vazios; chaves públicas preservadas. Verificação: omitido/null/vazio, objetos/arrays, bool ID, Unicode/card número. Dependências E03/E04/E09. Contrato: entradas incompatíveis passam a 400.

### E11 — AP-11 — LOW — valores sem nomes

Evidência: AppManager.js:46–48/:108–109 prefixo 4/PAID/DENIED espalhados; utils.js:6 porta fixa. Correção: constantes de domínio e porta configurável padrão 3000. Verificação: prefixos/estados/porta padrão e override. Dependência E02. Contrato preservado; não inserir pagamento real.

### E12 — AP-12 — LOW — nomes opacos

Evidência: AppManager.js:26–33/:52/:89/:102 self/u/e/p/cid/cc/enrId/c/enr. Impacto: leitura de identidade/financeiro difícil. Correção: nomes internos claros/adaptador. Verificação: mapeamento/contratos. Sem dependência obrigatória. Chaves usr/eml/pwd/c_id/card preservadas.

### E13 — AP-12 — LOW — código/estado sem consumidor

Evidência: AppManager.js:2 importa totalRevenue não usado; utils.js:10/:25 declara/exporta; cache :9/:12–15 só é escrito, nunca lido nas fontes; dbUser/dbPass/smtpUser sem consumidores. Pesquisa integral confirmou. Impacto: ruído/estado global sem finalidade. Correção: remover mortos/cache sem leitor, preservar log útil seguro. Verificação: referências, boot/checkout. Dependências E01/E02 conforme extração. HTTP preservado, estado interno/logs mudam.

Nenhuma SQL injection confirmada: valores HTTP usam placeholders. AP-09 duplicação não confirmada. Nenhuma API deprecated confirmada sem fonte/versão aplicável; nenhuma alegação de audit de dependências realizado na Fase 2.

## MVC e sequência aprovada

app fábrica/composição; server inicialização/listen/shutdown; config; routes HTTP; controllers casos de uso; models SQL sem req/res; services checkout e exclusão para transações; database conexão/fila; middleware autenticação/erros. Relatório pode usar controller/model especializado sem serviço pass-through. Checkout → controller → serviço → models → commit → HTTP. Relatório → identidade admin → controller → model. DELETE → identidade/ownership → controller → serviço → model.

Ordem: caracterizar original em isolamento; separar MVC; ciclo de vida/erros; fila e transações; hash/identidade/reset/retencão; leitura financeira em conjunto; regressão/reauditoria/documentação. Checkpoints em evidências, sem commits nesta execução.

## Política exata aprovada

Checkout novo permanece público com senha válida obrigatória; checkout existente confere pwd da conta eml atual, 401 se inválida e 403 se inativa. GET financeiro e DELETE usam Basic; senha verificada com hash moderno, conta ativa e role atual consultadas no banco a cada requisição. Transporte protegido fora do loopback. GET apenas admin. DELETE titular ou admin; vínculos históricos → desativar preservando dados, sem vínculos → excluir. IDs ausentes mantêm 200 idempotente após autorização; titular não ganha acesso sobre outro ID inexistente. Administrador inicial e reset por comando operacional explícito, sem senha padrão e sem role vinda do HTTP. Formato truncado exige reset confiável, sem upgrade por prefixo e sem fallback após hash moderno falhar. Sem novos endpoints.

## Todas as diferenças intencionais

| Superfície | Antes → depois aprovado | Verificação |
|---|---|---|
| Checkout novo sem senha | padrão implícito → 400 | omitido/null/vazio e sucesso |
| Entradas incompatíveis | truthiness/crash → 400 | tipos/arrays/Unicode |
| Email existente | sem prova → pwd correto, 401 inválida/403 inativa | sucesso persistido e negativas |
| Recusa | pode deixar conta → mesmo 400 Pagamento recusado sem novas linhas | contagens antes/depois |
| Erro consulta curso | 404 → 500; ausente/inativo mantém 404 Curso não encontrado | erro vs ausência |
| Auditoria/commit falhos | parcial/200 → rollback/500 | falhas intermediárias |
| GET financeiro | público → Basic admin; 401/403; 200 mesma forma/regra | sucesso/negativas |
| DELETE | público → Basic titular/admin | sucesso/negativas |
| DELETE com vínculo | órfão → desativação preservando histórico | conta inativa e financeiro |
| DELETE sem vínculo | físico → físico | efeito persistido |
| Texto DELETE | texto de sujeira → 200 Usuário removido. em exclusão/desativação/repetição autorizada | corpo/status |
| ID malformado | valor SQL → 400 | tipos/limites |
| Erro DB DELETE/relatório | falso sucesso/crash → 500 controlado | injeção de falha |
| Bootstrap/logs | seed literal/cartão → bootstrap explícito/log seguro | boot/logs |

Preservar métodos/caminhos, chaves públicas, 200 checkout com enrollment_id, prefixo 4 simulado, curso inativo no relatório, revenue só PAID, paid independente de status, curso vazio, Unknown para órfão existente, matrículas repetidas. Não adicionar unicidade matrícula, cascata financeira, anonimização, ordenação pública ou gateway real.

## Migração, rollback e limites

Usar bancos descartáveis e fixtures para caracterização/testes. Qualquer banco persistente exige backup integral antes de migração. Schema de contas adiciona hash reconhecível/active/role; reset explícito para formato truncado, sem hash do próprio truncamento. Preservar financeiros e dados de conta; órfãos existentes continuam Unknown, sem atribuir dono fictício. Não introduzir FK incompatível ou limpar histórico sem migração específica. Vários pagamentos por matrícula: original usa get sem ORDER BY, não autoriza somar todos; caracterizar escolha e evitar multiplicação. Transação cobre leitura/decisão/escrita inteira, inclusive concorrência entre DELETE/checkout. Testar toda escrita/auditoria/commit, todos os caminhos com sucesso autorizado, log/cleanup.

Rollback: código por checkpoint e cópia integral do banco antes de migração persistente; original :memory: perde dados ao reiniciar por definição. Não prometer recuperar memória encerrada. Se arquivo persistente for usado para operações/testes, é configuração explícita; padrão permanece :memory:. Não reintroduzir senha padrão/verificação truncada em ambiente exposto num rollback de autenticação.

Seleção original permitia E01–E13 ou severidade com dependências; humano aprovou todos. E03/E04 grupo identidade/credenciais; E05 requer E06/E09; E07 requer E04/E06/E09. Implementação, regressões e documentação pertencem à mesma execução da skill.
