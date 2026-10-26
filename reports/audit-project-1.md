# Auditoria aprovada — projeto 1

Data: 2026-10-23. Projeto: `code-smells-project`. Execução real da [skill local](../code-smells-project/.agents/skills/refactor-arch/SKILL.md), fases 1 e 2 somente leitura, seguida de aprovação humana.

## Aprovação e rechecagem antes das alterações

Resposta humana, recebida em 2026-10-23: **“Aprovo o escopo completo apresentado”**.

Escopo aprovado: todos os achados **F01–F16**, plano MVC, diferenças contratuais, dependências e decisões de migração abaixo. Nenhuma aprovação anterior genérica foi usada.

Rechecagem pré-edição: árvore de trabalho limpa. Os quatro hashes de fontes abaixo coincidiram integralmente. Este relatório foi persistido ANTES de qualquer edição de aplicação. Não houve instalação, importação, boot, seed ou acesso ao banco nas fases 1/2.

Skill SHA-256: `5113639E569AE7CB391CCD924971C31A9B06F9F3994D3A9724B4F9E4E8BDB937`. Referências lidas: project-analysis, anti-patterns, audit-report-template, mvc-guidelines, delivery, regression-checks, refactoring-playbook; validation lida na continuação aprovada.

## Fase 1 — análise

Linguagem Python (runtime não verificado na auditoria); Flask **declarado** 3.1.1 e Flask-Cors **declarado** 5.0.1, versões instaladas não verificadas. SQLite via sqlite3 padrão, versão não verificada. Banco relativo `loja.db`. Domínio: loja, produtos, usuários/login, pedidos e relatório. Entrada `app.py`, objeto global app e execução documentada `python app.py`.

Quatro fontes analisadas: app.py, controllers.py, models.py, database.py. Manifesto e README local também analisados. Excluídos ambientes virtuais, caches, bytecode, dados locais, diretórios sem fontes atuais, outros projetos e material histórico. 19 contratos explícitos, HEAD/OPTIONS automáticos excluídos. Nenhuma alegação de funcionamento executável nesta fase.

| Fonte | SHA-256 original |
|---|---|
| app.py | B106B109BF2D2114A23CFA2BE91F4654781A75239350FC64844217BA7E394EE6 |
| controllers.py | EDFF36072F19B4B8E471BF6AA35CCA0FFAA09495636A7D9BCC807447BB7EEFD6 |
| models.py | 6ADE3BCA1638A7A3A26C565D3DD34F0EB4F34DB2615E57315BB5373C4789F111 |
| database.py | 2327FD05C963F243C86182287141D264F2960FF8C8A3512CB95EF13CF91FD4D7 |
| requirements.txt | 9920665BD7C8D475DEE2EEE94465F9F02B2ECD834B1975A058A0206CD91CDDE4 |

Arquitetura parcial: app.py compõe Flask e registra rotas mas implementa SQL administrativo; controllers.py adapta HTTP, valida, simula notificações e consulta saúde; models.py combina SQL, serialização, autenticação, estoque, checkout e cálculo; database.py mantém conexão global, cria esquema e popula dados. Não é uma God Class CRITICAL: existe separação inicial, embora insuficiente.

Rastreio por domínio: produtos app.py:11–16 → controllers.py:5–126 → models.py:4–70,285–314; usuários/login app.py:18–21 → controllers.py:128–186 → models.py:72–131; pedidos app.py:23–26 → controllers.py:188–255 → models.py:133–233,275–283; relatório app.py:28 → controllers.py:257–262 → models.py:235–273; saúde/admin controllers.py:264–292 e app.py:47–78 → SQL direto. Todos dependem de get_db global.

## Contratos originais

| Método/caminho exato | Entrada | Sucesso/efeitos originais |
|---|---|---|
| GET / | — | 200 mensagem,versao,endpoints |
| GET /produtos | — | 200 dados,sucesso |
| GET /produtos/busca | q,categoria,preco_min,preco_max | 200 dados,total,sucesso |
| GET /produtos/<int:id> | ID | 200 dados,sucesso; 404 ausente |
| POST /produtos | nome,preco,estoque; descricao/categoria opcionais | 201 dados.id,sucesso,mensagem; insere |
| PUT /produtos/<int:id> | mesmos obrigatórios do POST | 200 sucesso,mensagem; atualiza; 404 ausente |
| DELETE /produtos/<int:id> | ID | 200 sucesso,mensagem; exclui; 404 ausente |
| GET /usuarios | — | 200 dados,sucesso; inclui senha |
| GET /usuarios/<int:id> | ID | 200 dados,sucesso incluindo senha; 404 ausente |
| POST /usuarios | nome,email,senha | 201 dados.id,sucesso; insere cliente |
| POST /login | email,senha | 200 dados(id,nome,email,tipo),sucesso,mensagem; 401 inválido; sem credencial |
| POST /pedidos | usuario_id,itens[{produto_id,quantidade}] | 201 dados(pedido_id,total),sucesso,mensagem; pedido/itens/baixa; recusa 400 |
| GET /pedidos | — | 200 dados,sucesso; itens e nome de produto |
| GET /pedidos/usuario/<int:usuario_id> | ID | 200 dados,sucesso; mesma estrutura |
| PUT /pedidos/<int:pedido_id>/status | status | 200 sucesso,mensagem mesmo se inexistente; pendente/aprovado/enviado/entregue/cancelado |
| GET /relatorios/vendas | — | 200 dados,sucesso; contagens/faturamento/desconto/ticket |
| GET /health | — | 200 status,database,counts,versao,ambiente,db_path,debug,secret_key |
| POST /admin/reset-db | — | 200 mensagem,sucesso; apaga itens,pedidos,produtos,usuarios |
| POST /admin/query | sql | SELECT 200 dados,sucesso; outros commit+200 mensagem,sucesso; vazio400; erro500 |

Produtos: id,nome,descricao,preco,estoque,categoria,ativo,criado_em. Pedidos: id,usuario_id,status,total,criado_em,itens. Itens: produto_id,produto_nome,quantidade,preco_unitario; produto ausente tem nome Desconhecido. Usuários de lista/detalhe: id,nome,email,senha,tipo,criado_em.

## Fase 2 — achados confirmados

**16 achados: CRITICAL 3 | HIGH 6 | MEDIUM 5 | LOW 2.** Não há deprecation confirmado: nenhum caso relevante de ORM/data e runtime ainda não verificado. Não foi fabricado AP-10. Evidências abaixo referem-se exclusivamente às linhas originais da revisão acima.

### F01 — CRITICAL — AP-01 — SQL Injection de domínio

Evidência: models.py:47–60,109–110,126–128,139–165,289–299. Nome/descrição/email/senha/termo/categoria e valores de itens entram em SQL por concatenação. Login/busca podem alterar condição; apóstrofos legítimos também quebram consultas. Correção: bind de todos os valores de domínio, mantendo LIKE/coringas/filtros. Verificação: login válido/inválido/bypass; apóstrofos, Unicode, %, _, POST/PUT/itens maliciosos e persistência. Dependência: nenhuma para parametrizar, testes compartilhados com F12. Contrato: legítimo preservado; dados deixam de alterar sintaxe. Console admin arbitrário pertence a F05.

### F02 — CRITICAL — AP-02 — Senhas expostas

Evidência: models.py:72–103 (83,99), controllers.py:128–144. GET usuários expõe senha armazenada a qualquer solicitante; rubrica de dados sensíveis implica CRITICAL. Correção: serializers sem senha ou hash. Verificação: lista/detalhe, legado/novo e sentinelas ausentes do JSON/log. Dependências: nenhuma para remoção; armazenamento em F04. Contrato: remove dados[*].senha e dados.senha.

### F03 — CRITICAL — AP-02 — Segredo/credenciais embutidos

Evidência: app.py:7, controllers.py:276–289, database.py:56–84. Health publica segredo; seed insere contas conhecidas inclusive admin quando produtos estão vazios. Credenciais são operacionais, não placeholders inertes. Correção: segredo externo, health sem segredo, seed explícito descartável sem admin fixo. Verificação: configuração ausente/presente, sentinelas, ausência de contas automáticas, seed isolado. Dependências F14,F05; implantação exige rotação. Contrato: remove secret_key, muda startup/provisão; não apaga contas existentes.

### F04 — HIGH — AP-04 — Senhas em texto puro

Evidência: models.py:105–110,122–130; database.py:75–82. Banco revela credenciais. Correção: hash adaptativo salgado compatível com runtime; upgrade legado após login válido com cutoff explícito; nunca fallback após falha em hash moderno. Verificação: senha certa/errada/Unicode, salts, upgrade persistido, hash moderno inválido. Dependências F01,F03. Contrato de entrada preservado; armazenamento muda, upgrade transacional.

### F05 — HIGH — AP-05 — Ausência de autenticação/autorização

Evidência: app.py:11–30,47–78, controllers.py:167–183,188–255; não há identidade, papel, propriedade ou middleware. Anônimo altera catálogo/status, lê terceiros, reseta ou executa SQL. Correção aprovada: Bearer assinado/expirável, usuário/papel atuais. Admin: escrita catálogo, lista global usuários/pedidos, relatório, status e ambas admin. Proprietário/admin: usuário individual/pedidos por usuário. Pedido: próprio usuario_id ou admin. Públicos: catálogo leitura, cadastro/login, raiz, saúde saneada. Preservar SQL arbitrário com admin verificado. Verificação: anônimo/proprietário/terceiro/admin; adulteração/expiração/conta ausente/papel alterado; sucesso persistido inclusive SQL escrita/reset. Dependências F01,F03,F04,F06,F07. Contrato: login adiciona token/expires_in; protegidos exigem Bearer e retornam401/403. Expiração configurável.

### F06 — HIGH — AP-06 — Conexão global mutável

Evidência: database.py:4–12,86, check_same_thread=False e ausência de teardown. Estado transacional compartilhado; commit de outro request pode confirmar trabalho pendente. Correção: conexão por contexto, teardown, caminho configurável, init separada. Verificação: contextos distintos, fechamento sucesso/erro, concorrência, bancos isolados. Dependências F14 e F07. HTTP preservado; lifecycle/configuração mudam.

### F07 — HIGH — AP-07 — Checkout sem consistência/rollback

Evidência: models.py:133–168 e controllers.py:218–220. Leitura de estoque antes de escrita; repetidos não acumulados; preço reconsultado; sem rollback explícito. Repetidos/concorrência podem negativar estoque; erro intermediário deixa escrita pendente sujeita a commit posterior global. Correção: transação de leitura/decisão/escrita, demanda acumulada, preço consistente, rollback e exclusão de interleaving. Verificação: repetidos, simultâneos, falha em cada escrita e leitura por request posterior. Dependências F06/F12. Contrato: válidos preservados; demanda incompatível recusada sem resíduo. Linhas repetidas podem permanecer distintas.

### F08 — HIGH — AP-03 — MVC incompleto/acoplamento

Evidência: app.py:47–78 e controllers.py:264–274 SQL em HTTP; controllers.py:24–93,188–250 regras/notificações; models.py:133–168,235–272 orquestração/cálculo; imports globais app.py:3–4,controllers.py:2–3,models.py:1. Correção: rotas/controller/model explícitos, DI, serviço de checkout significativo, configuração/auth separados. Verificação: fluxo por domínio, testes com DI, sem SQL nas rotas/HTTP nos models/ciclos. Dependências F06/F07. Contrato preservado salvo diferenças selecionadas.

### F09 — HIGH — AP-05/configuração — Debug em interface externa

Evidência: app.py:8,88, debug=True e 0.0.0.0. Debugger de desenvolvimento exposto em interface de rede. Correção: debug false por padrão, modo dev explícito, host/porta configuráveis. Verificação: boot real/erro sem debugger e configuração dev. Dependência: nenhuma obrigatória; composição F08 facilita. Contrato operacional muda; health informa debug real.

### F10 — MEDIUM — AP-08 — N+1

Evidência: models.py:171–233 consulta itens por pedido/produto por item;139–155 duas buscas por item no checkout. Correção: lotes/joins e carregamento único transacional. Verificação: SELECTs com1/20 pedidos, vazio, duplicatas, produto ausente/Desconhecido, ordem, sem multiplicação. Dependência F07 no checkout; listagens independentes. Contrato preservado.

### F11 — MEDIUM — AP-09 — Validação/serialização duplicada divergente

Evidência: controllers.py:28–54 vs72–90 (PUT sem comprimento/categoria); models.py:12–21,31–40,304–313,178–200,211–232,79–102. Correção: validadores/serializadores compartilhados; aplicar limites/categorias POST ao PUT. Verificação:1/2/200/201, categorias, omissão/null/vazio, campos. Dependências F02,F12. Extração preserva; PUT mais estrito é diferença aprovada.

### F12 — MEDIUM — AP-09/validação — Estrutura/tipos/domínio

Evidência: controllers.py:37–50,81–90,118–121,153–158,169–174,195–203,239–243;models.py:139–165;database.py:27–52 sem integridade referencial. Tipos geram500; quantidades negativas aumentam estoque, zero/fração/bool passam inconsistentemente; usuario_id não tem existência consultada. Correção: objeto JSON, coleção/itens adequados, textos string; preço numérico finito>=0 sem bool; estoque inteiro>=0 sem bool; IDs/quantidades inteiros>0; usuário existente; filtros numéricos válidos. Sem nova política de email único/status. Verificação: omissão/null/vazio/malformado, objeto/array, bool/string numérica/NaN/infinito, quantidades e usuário ausente; sem escrita. Dependências F07,F11; não substitui F01. Contrato: inválidos antes aceitos/500 passam400.

### F13 — MEDIUM — AP-02/erros — Exceções internas públicas

Evidência: app.py:77–78;controllers.py:10–12,60–62,125–126,164–165,218–220,291–292 e demais handlers. Correção: erro central com mensagem genérica pública, logging interno sem credenciais; manter erros de negócio conhecidos. Verificação: DB/conversão/JSON/exceção sentinela e envelopes. Dependência F12. Contrato:500 genérico, inválidos400.

### F14 — MEDIUM — AP-06/lifecycle — Init/seed em get_db

Evidência: database.py:7–84, app.py:82. Contagem de produtos governa inserção também de usuários. Leitura inicial escreve; reinício após reset repopula; base com usuários e sem produtos pode duplicá-los. Correção: conexão sem init, comandos explícitos init/migração/seed. Verificação: leitura sem seed, reset/restart, init idempotente, seed só descartável explicitamente escolhido. Dependências F03/F06. Contrato: init explícita e reset durável após reinício.

### F15 — LOW — AP-11 — Valores de domínio sem nomes

Evidência: models.py:256–262, controllers.py:52,242,41/85. Correção: constantes/tabela de faixas, preservar ordem, comparação estrita/arredondamento. Verificação: abaixo/igual/acima de1000/5000/10000, zero/vazio, mesmas categorias/status. Sem dependência. Contrato preservado; não muda desconto nem inclusão de cancelados.

### F16 — LOW — AP-12 — Imports sem uso

Evidência: models.py:2 sqlite3, database.py:2 os; busca nas fontes confirmou ausência de uso. Correção: remover somente esses imports. Verificação: busca e boot. Sem dependência. Contrato preservado.

## Plano MVC aprovado

Composição/create_app e entrada; configuração validada; banco por contexto e transações; routes/ por domínio adaptando HTTP; controllers/ coordenando casos; models/ encapsulando SQL; serviço checkout para coordenação transacional; auth/validators/serializers separados. Nada de serviços pass-through. A estrutura exata pode adaptar-se à análise original sem alterar contratos.

Ordem: recheck/auditoria aprovada → baseline descartável19 contratos → F01/F02/configuração → F03/F06/F14 → F04/F05 → F07/F12 → MVC/duplicação/N+1/erros → LOW → reauditoria, boot e matriz completa com sucesso autorizado e negação. Cada fatia tem RED/GREEN e ponto de rollback; achados futuros não ampliam escopo automaticamente.

## Diferenças contratuais aprovadas

| Superfície | Antes → depois | Testes |
|---|---|---|
| SQL domínio F01 | concatenação → valores bindados | injeção/apóstrofos/LIKE |
| GET usuários lista/detalhe F02 | senha → campo removido | demais campos e sentinelas |
| GET health F03/F09 | secret_key/debug fixo → sem segredo/debug configurado | contagens/versão preservados |
| POST login F05 | usuário apenas → campos existentes + token/expires_in superiores | login/expiração/adulteração |
| Catálogo escrita/listas globais/relatório/status/admin F05 | anônimo → admin |401/403 e sucesso persistido |
| Usuário individual/pedidos por usuário F05 | público → proprietário/admin | papéis/propriedade |
| POST pedidos F05 | usuario_id confiado → próprio ou admin | identidade vs corpo |
| Entradas JSON/filtros F12/F13 | inválidos aceitos/500 →400 | matriz tipos/null/omissão/malformado |
| PUT produto F11 | sem comprimento/categoria → regras POST | limites/categorias |
| POST pedidos F07/F12 | inválidos/cumulativos/órfãos/parciais →400 sem resíduo | repetidos/concorrência/falhas |
| Erros inesperados F13 | exceção crua →500 genérico | sentinelas/envelope |
| Inicialização F03/F14 | seed automático → init explícita/seed optativo | vazio/existente/reinício |
| Execução F09 | debug e bind fixos → debug false/configuração | boot/erro |
| Senhas F04 | texto puro → hash/upgrade legado controlado | login/persistência |

Preservar:19 métodos/caminhos; admin SQL arbitrário verificado (inclusive escrita); DELETE físico; status inexistente200; cancelamento sem reposição real; estados aceitos; faturamento incluindo cancelados; Desconhecido; datas/moeda/arredondamento; notificações locais simuladas. Não introduzir email único, transições de status, reposição de estoque, novos FKs ou coluna ativo de usuário.

## Migração/rollback e dependências

Banco existente só com backup verificável, plano aprovado e ensaio em cópia; preferir descartáveis. Preservar IDs/timestamps/preços/relações; nunca reset para migrar. Remover credenciais do código não apaga/redefine contas existentes; rotação/reset precisa decisão. Hash cabe em TEXT, mas código antigo não autentica hashes: rollback exige código compatível ou backup com impacto em escritas posteriores. Sem FKs/UNIQUE automáticos. Relatar inconsistências sem saneamento silencioso. Documentar config/init junto ao lifecycle.

Grupos aprovados: F03+F06+F14; F05 depende F01/F03/F04; F07 depende F06/F12; F11/F12 coordenados. F02, listagens F10, F15/F16 podem ser isolados. Todas as dependências e diferenças foram abrangidas pela aprovação completa.

Este é o relatório aprovado da auditoria do projeto 1. A Fase 2 parou e a aprovação humana real acima abriu a Fase 3. A execução e a reauditoria estão registradas na [validação do projeto 1](validation-project-1.md).
