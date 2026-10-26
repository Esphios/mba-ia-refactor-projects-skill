# Validação — ecommerce-api-legacy

Execução da Fase 3 de `refactor-arch` em 2026-10-23. Aprovação humana: **“Aprovo o escopo completo apresentado”**. A [auditoria completa](audit-project-2.md) foi salva com revisão/hashes/escopo/aprovação antes de editar fontes. O executor isolado não fez commit nem publicação; a integração final foi serializada pelo executor principal.

## Resultado medido

- **21/21 testes passam**, nenhum skip/cancelado; `npm test`, depois de novo `npm ci`.
- **42 requisições verificadas**, cobrindo os **3 métodos/caminhos originais**, com sucesso administrativo/do titular e recusas: `npm run test:http` (script equivalente executado para JSON puro: `node test/http-matrix.cjs`).
- Boot real: `node src/server.js`, filho Node **PID 6476**, porta efêmera **54074**, loopback, readiness máximo **10 segundos**. Processo encerrado por IPC, **exit 0**, banco temporário removido depois do término; `cleanup:true`.
- Runtime verificado: **Node v24.12.0**, **npm 11.19.1**, **Express 4.22.1**, **sqlite3 5.1.7**; módulo nativo executado, não apenas versão do manifest.
- Três fontes originais → **18 fontes** em `src/`, com MVC explícito, infra/config/security separadas, 2 comandos operacionais e 5 arquivos de teste/suporte/runner.
- Nenhuma chamada de pagamento/email real; regra simulada de prefixo `4` mantida.

Não significa ausência de risco geral: **npm audit continua apontando 14 advisories do lock original** (2 critical, 8 high, 1 moderate, 3 low). São residuais fora dos E01–E13 aprovados; incluem cadeias de instalação/build de sqlite3/node-gyp/tar e dependências transitivas Express. O coordenador instruiu conservar versões compatíveis e registrar o risco separado. Não houve force upgrade nem alegação de zero vulnerabilidades.

## Baseline e RED antes da implementação

O original foi executado diretamente dos três arquivos inspecionados, com banco `:memory:` descartável e listener local efêmero; nenhuma cópia de solução foi usada. O probe temporário `node test/characterize.cjs` confirmou os três endpoints e efeitos e foi retirado após registrar [baseline JSON](evidence/skill-run-project-2-baseline.json), porque dependia do AppManager removido. O pacote final contém runners somente da aplicação atual.

O baseline observou checkout 200 e matrícula/pagamento/auditoria; recusa 400 **deixando usuário criado**; DELETE público 200 **removendo somente usuário e mantendo pagamentos órfãos**; relatório com curso vazio e receita original. A ordem de cursos capturada era Docker/Clean Architecture, consequência dos callbacks, sem ORDER BY ou garantia pública. A versão final compara o conteúdo por course, sem forçar uma política nova de ordem. Não é alegada equivalência de ordem incidental.

Em seguida `node --test --test-concurrency=1 test/security.test.cjs` executou **5 testes, 0 passaram/5 falharam** com o original: relatório público 200 em vez de 401; checkout com senha errada 200; conta criada após recusa; DELETE anônimo 200; cartão aparecendo em log. [Saída RED sanitizada](evidence/skill-run-project-2-red.txt). Nenhuma fonte de aplicação tinha sido alterada nesse momento.

## Mapeamento audit → transformação → verificação

| Achado | Transformação nesta execução | Evidência |
|---|---|---|
| E01 CRITICAL | Removidos cartão/chave de logs e config de credenciais fictícias; demo sem senha utilizável; admin só por comando explícito | Teste de captura de logs; HTTP verifica respostas sem senha/hash/cartão; log do boot contém só event/pid/port |
| E02 CRITICAL | Removido AppManager; fábrica/composição e server separados; routes/controllers/models explícitos; serviços para transações | Trace estático de imports; 3 endpoints exercitados pela aplicação real |
| E03 HIGH | scrypt com salt aleatório, verificação completa Unicode, sem padrão/legado truncado/plaintext fallback; reset confiável | Hashes distintos, senha errada/prefixo igual, migração e comando reset executados sobre arquivo descartável |
| E04 HIGH | Basic nos protegidos; pwd no checkout existente; active/role atuais no mesmo limite da operação; titular/admin no DELETE | Anônimo 401, terceiro 403, admin GET 200; titular DELETE físico e desativação 200; alteração de role/active entre pedidos imediatamente aplicada |
| E05 HIGH | BEGIN IMMEDIATE → leitura/decisão/todas escritas → COMMIT; rollback em qualquer erro; recusa antes de escritas | Triggers reais falhando users/enrollments/payments/audit_logs; FK deferred induz falha no COMMIT; sem resíduos; checkout concorrente não duplica conta |
| E06 HIGH | Abertura/schema aguardados antes de listen; fila cobre operação assíncrona completa, inclusive reads; close aguarda fila | Leitura não observa escrita revertida; init com caminho inválido rejeita; boot/shutdown reais e concorrência |
| E07 HIGH | Conta com matrículas desativada preservando dados e financeiros; sem vínculos removida; leitura e decisão transacionais; IDs novos pulam referências órfãs | Soma/contagem payments preservadas, nome mantido; novas ações de inativo 403; corrida DELETE/checkout; órfão continua Unknown após checkout/provisão |
| E08 MEDIUM | Um SELECT em conjunto com LEFT JOIN e lookup de um pagamento, índices enrollment/course e payment/enrollment | 1 statement no model com 1 e 20 matrículas; vazio/inativo/órfão/sem pagamento/não PAID/duplicata/null/zero; HTTP inclui mais 1 SELECT de identidade, total constante 2 |
| E09 MEDIUM | Promises de callbacks e mapper central; sem sucesso falso ou detalhes SQLite no HTTP | Falha consulta curso/report/DELETE 500 controlada; mensagens originais Erro ao criar usuário/Erro Matrícula/Erro Pagamento preservadas; auditoria/commit 500 Erro DB |
| E10 MEDIUM | Validação de corpo/tipos/IDs/senha; chaves originais mantidas | Omitido/null/vazio/arrays/objetos/bool/card numérico/JSON inválido e Unicode |
| E11 LOW | Estados/prefixo nomeados, porta/host/banco/demo configuráveis | Prefixos aceito/recusado, server real com PORT=0, padrão 3000 no config |
| E12 LOW | Nomes internos claros no adaptador/casos/models | Contrato original usr/eml/pwd/c_id/card e resposta Sucesso/enrollment_id |
| E13 LOW | Removidos totalRevenue/globalCache/config sem consumidores e imports mortos | Busca de referências + imports/boot/testes atuais; sem estado global de negócio |

Todos os **13 achados iniciais** foram tratados dentro da skill: **2 CRITICAL, 5 HIGH, 3 MEDIUM e 3 LOW**. Não foram fabricados novos achados para satisfazer contagem mínima. API deprecated não confirmada no código atual. SQL HTTP permanece parametrizado; não havia SQL injection confirmada no original.

## Matriz de contratos e efeitos

| Original | Resultado validado |
|---|---|
| POST /api/checkout | Novo/existente autenticado 200 com msg/enrollment_id, matrícula/pagamento/auditoria commitados; senha errada 401, inativo 403, curso ausente 404, input inválido/JSON inválido 400, recusa 400 sem novas linhas, falhas 500 sem resíduos |
| GET /api/admin/financial-report | Admin atual 200, sem credencial/Basic inválido/senha errada 401, comum/inativo 403. Todos os cursos, receita somente PAID, paid inclusive não PAID, Unknown e 0 para ausência, null/zero preservados, sem multiplicação por vários payments |
| DELETE /api/users/:id | Sem Basic 401, terceiro 403, ID inválido 400; titular/admin 200 Usuário removido.; desativação com vínculo, exclusão física sem vínculo, repetição/inexistente autorizada pelo admin 200; pagamentos/dados históricos retidos |

Métodos incorretos e caminho desconhecido seguem comportamento Express 404. O runner não inventa HEAD/OPTIONS como novos endpoints. Basic é a política explicitamente aprovada; não há JWT/login/novo endpoint. Basic consulta estado atual em cada chamada, não possui token com expiração a testar. Conta desativada não consegue repetir DELETE como titular: 200 idempotente depende de outra identidade autorizada (admin ativo).

Sem alteração comercial: aceita prefixo 4, mantém matrículas repetidas e cursos inativos no relatório, não soma todos os pagamentos duplicados nem cria ordenação pública. LEFT JOIN mantém histórico ausente. ORDER BY não foi adicionado para imitar callback incidental.

## Sequência, correções e limites

1. Recheck de revisão/árvore/hashes; auditoria/aprovação persistidas.
2. `npm ci`: sucesso, nativo sqlite3 carregou; advisories registrados sem mudar dependências.
3. Baseline original e cinco falhas RED de comportamento reais.
4. MVC, fila transacional, identidade/hash, retenção, leitura em conjunto → primeira suíte 12/12.
5. Migração/reset/commit failure/query count/boot failure → 16/16.
6. A revisão detectou que mapper genérico apagava mensagens 500 legadas. Asserção adicionada falhou (Erro DB em vez de Erro ao criar usuário); corrigido mapeamento seguro por etapa e preservado rollback. Suíte verde.
7. Investigada ordem incidental do relatório. Não se consolidou ordenação nova; retirada tentativa de imitar timing de callback conforme escopo aprovado. Comparação por chave do curso, sem declaração de ordem garantida.
8. Erros reais no DELETE/report/curso e null/zero/vazio financeiro adicionados → 18/18.
9. Revisão independente reproduziu reutilização de ID referenciado por matrícula órfã, que atribuía histórico `Unknown` a uma conta nova. Dois testes RED cobriram checkout e provisão; criação transacional passou a escolher ID acima de `users.id` e `enrollments.user_id` → 20/20.
10. A mesma revisão reproduziu matrícula nova reutilizando `payments.enrollment_id` órfão: pagamento legado 777 passava a pertencer à aluna e ocultava o atual 497. Um terceiro RED levou a matrícula a reservar IDs referenciados em payments. Revisor repetiu probe, 21/21 e HTTP 42/42: órfão segue sem dono e pagamento atual aparece corretamente.
11. Lockfile atualizado **somente no metadata engines >=22**; `git diff` confirmou nenhuma alteração de versão de dependência. Novo `npm ci` passou, seguido de suíte e HTTP completos.
12. Releitura de regression-checks e revisão estática de limites/imports/fluxos, finalização de documentação/evidências. Não houve reset/clean/stage/commit nem alteração de outro projeto.

O resultado é verificação local da execução atual. O teste não substitui revisão independente, load test ou validação de implantação/TLS. O original não tinha persistência em disco; todos os arquivos utilizados aqui eram descartáveis. No uso de arquivo real, operador deve parar serviço e fazer backup antes de migração/reset. `account` é ferramenta administrativa confiável, não autorização HTTP.

## Migração/rollback reproduzíveis

Ver [README do projeto](../ecommerce-api-legacy/README.md). Migração aditiva preserva IDs/rows/valores existentes, adiciona active=1/role=user e índices; não aplica seed sem opção, não cria FK que invalide órfãos antigos e não apaga financeiro. Formato truncado exige reset por LMS_PASSWORD via comando. Reset não promove ou reativa. Duplicatas históricas de email não são mescladas silenciosamente; comando de reset exige exatamente uma conta, permitindo operador resolver identidade com evidência própria.

Rollback de arquivo: servidor parado, cópia integral do banco atual antes de restaurar cópia anterior correspondente à versão anterior. Não remover colunas isoladamente nem expor novamente senha padrão/truncada. Memória encerrada não tem recuperação prometida. Histórico financeiro não foi limpo, migrado para outro dono, anonimizado ou submetido a cascata.

## Evidências e comandos

- [Baseline original sanitizado](evidence/skill-run-project-2-baseline.json).
- [RED inicial sanitizado](evidence/skill-run-project-2-red.txt).
- [npm ci final](evidence/skill-run-project-2-install.txt).
- [Testes finais](evidence/skill-run-project-2-tests.txt).
- [RED](evidence/skill-run-project-2-orphan-id-red.txt) e [GREEN](evidence/skill-run-project-2-orphan-id-green.txt) para preservação de órfãos.
- [RED](evidence/skill-run-project-2-orphan-enrollment-red.txt) e [GREEN](evidence/skill-run-project-2-orphan-enrollment-green.txt) para IDs de matrícula/pagamentos órfãos.
- [HTTP, readiness, PID, porta e cleanup](evidence/skill-run-project-2-http.json).
- [npm audit inicial](evidence/skill-run-project-2-dependencies-before.json) e [final](evidence/skill-run-project-2-dependencies-after.json).
- [Manifesto SHA-256 da execução](evidence/skill-run-project-2-source-manifest.json).

Comandos a partir de ecommerce-api-legacy: `npm ci`, `npm test`, `npm run test:http`, `npm audit --json`. O último retorna código não zero pelos advisories conhecidos; não é apresentado como check de segurança aprovado. O runner usa child_process com windowsHide, porta dinâmica e finally para fechar banco/processo e remover somente seu diretório temporário.
