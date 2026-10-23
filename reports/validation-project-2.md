# Validação — projeto 2: ecommerce-api-legacy

Executado em 2026-10-22 no workspace entregue, sobre a revisão-base `6d1ce6248c3e956801010a89d8bdaab48029bf30` mais o diff de implementação. O [manifesto SHA-256](evidence/project-2-source-manifest.json) identifica precisamente os arquivos refatorados; o commit final será realizado pelo fluxo de entrega raiz. Não se usou outro repositório como evidência de execução.

## Autorização, auditoria e baseline

A auditoria independente registrou nove achados: 2 CRITICAL, 4 HIGH, 1 MEDIUM e 2 LOW. A [auditoria original](audit-project-2.md) foi arquivada antes da primeira alteração de código, com a autorização do usuário: **“ignore as aprovações por enquanto. continue até o fim.”** A [resposta independente bruta](evidence/audit-project-2-phase-1-2.md) permanece preservada. Essa instrução explícita prevaleceu sobre a pausa padrão da skill.

Política final de exclusão: remover fisicamente usuários sem relações; desativar usuários com matrículas, preservando todos os pagamentos, matrículas e logs. Nenhuma anonimização automática. A política substitui a opção de anonimização sugerida na auditoria.

Antes da implementação, foi instalado o lockfile original e executada [caracterização real dos três endpoints originais](evidence/project-2-baseline.log), usando Express e SQLite em memória, carregando `AppManager.js` da revisão-base via `git show` em uma VM isolada. O console do legado foi substituído por logger sem saída para evitar registrar cartão/chave. Foram observados checkout aprovado, recusado, entrada ausente, curso inexistente, relatório público e exclusão pública; os efeitos inseguros (usuário criado na recusa e matrícula órfã após exclusão) foram afirmados explicitamente. Não houve cobrança externa ou banco preexistente alterado.

Os testes do contrato aprovado foram escritos antes do novo código e sua [execução vermelha](evidence/project-2-red.log) falhou pela ausência das novas interfaces de segurança. A [execução vermelha da migração](evidence/project-2-migration-red.log) também antecedeu a implementação desse módulo. A primeira implementação passou 9/9 testes. Ao adicionar novos testes, uma leitura Python com encoding padrão corrompeu somente a string esperada em uma asserção; o [diagnóstico preservado](evidence/project-2-test-fixture-encoding-failure.log) foi corrigido com UTF-8 explícito. A suíte final passa 13/13, sem testes ignorados.

## Comandos e runtime observados

Executados na raiz do repositório:

```powershell
node --version
npm --version
npm ci --prefix ecommerce-api-legacy
npm test --prefix ecommerce-api-legacy
npm run test:http --prefix ecommerce-api-legacy
npm audit --json --prefix ecommerce-api-legacy
git diff --check -- ecommerce-api-legacy reports/audit-project-2.md
```

| Verificação | Esperado | Observado / evidência |
| --- | --- | --- |
| Runtime | Compatível com dependências instaladas | Node `v24.12.0`, npm `11.19.1`; Express `4.22.3`, sqlite3 `6.0.1`, SQLite `3.52.0` no [boot HTTP](evidence/project-2-http.log) |
| Instalação lockfile | Instalar dependências nativas e manter lock consistente | [npm ci](evidence/project-2-install.log): 124 pacotes adicionados, 125 auditados, zero vulnerabilidades |
| Testes | Todos os cenários aprovados passam | [npm test](evidence/project-2-tests.log): 13 pass, 0 fail, 0 skip |
| Boot real | Somente aceitar HTTP após schema e seed | Processo filho executa `src/server.js`; evento `ready` e primeira consulta HTTP válida no [log](evidence/project-2-http.log) |
| Falha de configuração | Não escutar sem segredo | Processo real sem AUTH_SECRET encerra com código 1; `STARTUP_FAILURE_PASS` no mesmo log |
| Encerramento | Fechar servidor/conexão e remover somente fixture | Evento `stopped`; runner valida que o diretório temporário pertence ao temp do SO antes de removê-lo |
| Supply chain | Nenhuma vulnerabilidade conhecida no lock final | [npm audit JSON](evidence/project-2-dependency-audit.json): total 0 |

## Inventário HTTP e resultados reais

Inventário original conferido: **3 pares método/caminho**, excluindo HEAD/OPTIONS automáticos. Inventário final: os mesmos 3, mais login. Todos são exercitados em processo real pelo comando `npm run test:http`; cada caso no [log HTTP](evidence/project-2-http.log) contém entrada de cenário, método, caminho, status esperado/observado e `passed:true`. Tokens e senhas não são impressos.

| Método / caminho | Entrada / acesso | Esperado e observado | Efeitos verificados |
| --- | --- | --- | --- |
| `POST /api/checkout` | `usr,eml,pwd,c_id,card`, conta nova válida | `200 {msg:"Sucesso",enrollment_id:1}` | Usuário scrypt, matrícula, pagamento PAID e auditoria persistidos |
| `POST /api/checkout` | Prefixo de cartão 5 | `400 Pagamento recusado` | Nenhuma conta ou matrícula adicional |
| `POST /api/checkout` | Corpo vazio, tipo de cartão numérico, senha ausente para conta nova | `400 Bad Request` | Nenhuma escrita |
| `POST /api/checkout` | Curso inexistente | `404 Curso não encontrado` | Nenhuma escrita |
| `POST /api/checkout` | Email existente sem prova ou senha errada | `401` | Nenhuma matrícula adicional |
| `POST /api/checkout` | Bearer válido do titular | `200`, mesma forma original | Nova matrícula/pagamento para o titular |
| `POST /api/checkout` | Falha induzida na gravação de pagamento | `500 Erro DB` | Contagens de users/enrollments/payments/audit iguais ao snapshot anterior |
| `POST /api/checkout` | Cinco requisições concorrentes no processo real | Todas `200` | Exatamente cinco pagamentos adicionais |
| `GET /api/admin/financial-report` | Sem Bearer / usuário comum / adulterado / expirado | `401 / 403 / 401 / 401` | Sem vazamento de dados |
| `GET /api/admin/financial-report` | Administrador ativo | `200`, array original com course/revenue/students e student/paid | Clean Architecture: receita 1994 e duas matrículas; Docker: receita 0, students vazio |
| `GET /api/admin/financial-report` | Tabela de cursos temporariamente indisponível | `500 Erro DB` | Sem travamento, SQL ou resposta parcial |
| `DELETE /api/users/:id` | Sem identidade / outro usuário / ID inválido / ausente | `401 / 403 / 400 / 404` | Sem alteração indevida |
| `DELETE /api/users/:id` | Titular com histórico financeiro | `200 {msg,id,action:"deactivated"}` | Estado ativo 0, duas matrículas e todos os pagamentos preservados; token passa a receber 401 |
| `DELETE /api/users/:id` | Administrador exclui conta sem relações | `200 {msg,id,action:"deleted"}` | Usuário realmente removido |
| `DELETE /api/users/:id` | Trigger induz erro de remoção | `500 Erro DB` | Sem falso sucesso |
| `POST /api/auth/login` | Admin e usuário com credenciais corretas | `200 {access_token,token_type:"Bearer",expires_in}` | Token verificável/expirável, sem senha/hash na resposta |
| `POST /api/auth/login` | Corpo inválido / senha errada | `400 / 401` | Nenhum token emitido |

A suíte acrescenta sucesso de exclusão física pelo próprio titular e desativação por administrador, demissão de role em tempo real, login desativado, confirmação de senha existente, falha em **cada uma** das quatro escritas de checkout, 12 compras concorrentes e quatro compras concorrentes do mesmo email (uma única conta). Também executa duas transações concorrentes com uma falha e outra bem-sucedida: somente as quatro linhas do checkout bem-sucedido permanecem.

## Rastreabilidade dos achados e reauditoria

| Achado | Correção e fronteira verificável | Evidência / resultado |
| --- | --- | --- |
| F-01 CRITICAL, segredos e logs | `config/index.js` exige segredo externo e credenciais externas para seed; logs somente evento/resultado/ID | Config ausente/inválida falha; captura de logs não contém cartão, senha ou segredo; exemplos não contêm credencial operacional |
| F-02 CRITICAL, God Class | `app.js` composição; `server.js` startup; `routes/index.js`; quatro controllers; três módulos de models; serviços específicos; validação/errors/db separados | `AppManager.js` e `utils.js` removidos. Routes sem SQL, models sem req/res. Traço checkout: route → checkoutController → checkoutService → checkoutModels/userModel → db |
| F-03 HIGH, senhas | scrypt 16384/8/1, salt aleatório de 16 bytes, derivação 64 bytes; comparação timingSafeEqual | Mesma senha produz hashes diferentes; senha errada/legado/malformado rejeitados; senha nova obrigatória; migração bloqueia credenciais antigas até reset explícito |
| F-04 HIGH, autorização | Login HMAC SHA-256 com expiração; authenticate recarrega usuário/role/active; adminOnly; ciclo de vida self/admin | Sucesso legítimo e 401/403 nos quatro caminhos; token adulterado/expirado/conta inativa rejeitado; privilégio não vem do corpo da requisição |
| F-05 HIGH, estado global e ciclo de vida | Uma conexão por aplicação com fila para todas as operações; transação inteira retém fila; close explícito; cache global sem consumidor removido | Aplicações/fixtures independentes; sucesso concorrente, mesma conta e mistura falha/sucesso sem interferência; shutdown real |
| F-06 HIGH, atomicidade e retenção | BEGIN IMMEDIATE/COMMIT/ROLLBACK para conta+matrícula+pagamento+audit; ciclo de vida transacional; FK RESTRICT no schema novo | Triggers de falha em users/enrollments/payments/audit_logs mantêm snapshot intacto; financeiro preservado em desativação; erro de delete não retorna sucesso |
| F-07 MEDIUM, N+1 | Um SELECT com joins e escolha do primeiro pagamento, usando índices; agrupamento mantém forma | 1 matrícula: **2 SELECTs HTTP totais**; 20 matrículas: **2 SELECTs** (1 auth + 1 relatório). Vazio, pagamento recusado/ausente, usuário histórico ausente e erro de query cobertos |
| F-08 LOW, magic values | `simulatedPaymentGateway.js` nomeia prefixo de aprovação; senha padrão removida | Prefixo 4 aprovado/5 recusado; senha nova ausente rejeitada |
| F-09 LOW, nomes e código morto | `validation/inputs.js` mapeia chaves públicas para nomes claros; totalRevenue e cache removidos | Request original e shape original de checkout/relatório preservados; nenhuma referência residual no código de produção |

Reauditoria local das fontes finais: os nove achados iniciais estão corrigidos no escopo aprovado. A estrutura final tem 24 arquivos de produção, em contraste com os três originais; a contagem exclui testes, node_modules, skill copiada e manifestos. Não se introduziu SQL de request por concatenação nem persistência dependente de HTTP. Os testes não usam cobrança real.

## Dados existentes, migração e rollback

O original usa memória, portanto não há arquivo de produção do repositório para migrar. A validação cria uma cópia legada descartável: o startup a rejeita de maneira explícita e fecha a conexão; o módulo de migração adiciona colunas sem mudar registros/totais financeiros e pode ser repetido. O formato de senha antigo não é inferido: `password_reset_required=1`, preservando o valor até reset operacional explícito. Após reset para scrypt, o login funciona. Um histórico órfão anterior permanece legível como `Unknown`/0 no relatório. Não se apagaram nem anonimizaram dados históricos.

O CLI `npm run migrate:legacy` requer DB_PATH de arquivo existente e copia backup não sobrescrevível antes de alterar. A execução contra dados reais permanece uma operação operacional a realizar com servidor parado e backup verificado; este trabalho só usou dados descartáveis. Para rollback, parar servidor, preservar o estado novo, restaurar `.pre-migration.bak` e a revisão anterior de código, conciliando operações financeiras ocorridas após o backup. Procedimento completo no [README do projeto](../ecommerce-api-legacy/README.md).

## Dependências e limites

O lockfile inicial apresentou [14 nós vulneráveis](evidence/project-2-dependency-audit-before.json): entre eles `proxy-addr` CRITICAL (spoofing de IP, GHSA-jqcg-44mw-7w3h) no runtime Express e `tar` CRITICAL (DoS de descompressão, GHSA-23hp-3jrh-7fpw) na cadeia de instalação do SQLite. `npm audit fix` e atualização do Express dentro da faixa existente eliminaram problemas de runtime, incluindo path-to-regexp, qs e body-parser, mas deixaram sete nós da cadeia de build: sqlite3/node-gyp/make-fetch-happen/cacache/tar/http-proxy-agent/@tootallnate/once. O JSON inicial registra cada advisory e fixAvailable; o [log de correção compatível](evidence/project-2-dependency-fix.log) registra a exigência de mudança major para sqlite3.

Com autorização explícita do fluxo raiz, sqlite3 foi atualizado de 5.1.7 para **6.0.1** para remover o risco conhecido da cadeia de instalação. Node 24 atende o mínimo >=20.17. O [log de upgrade](evidence/project-2-sqlite6-upgrade.log), a reinstalação por lockfile, a suíte completa e o boot real validam a mudança de major. O [audit final](evidence/project-2-dependency-audit.json) registra **0 vulnerabilidades conhecidas**. O instalador ainda avisa que prebuild-install está sem manutenção; isso é uma limitação da ferramenta de instalação upstream, sem advisory restante no audit atual.

Os testes comprovam os contratos e achados documentados; não constituem certificação de segurança de produção. O gateway é simulado, HTTP escuta localmente, SQLite em memória é descartável por padrão e o serviço não inclui rate limit de login ou um fluxo público de recuperação de conta. Migrações não apagam órfãos preexistentes nem adicionam retroativamente foreign keys às tabelas históricas. Nenhum segredo antigo foi validado externamente; eventual rotação em sistemas reais continua necessária.

## Checklist final

- [x] Auditoria arquivada antes do código e autorização explícita registrada.
- [x] Baseline real dos 3 endpoints em banco descartável e testes vermelhos antes das interfaces novas.
- [x] npm ci e versões nativas verificadas; zero vulnerabilidades conhecidas no lock final.
- [x] MVC explícito, app importável, startup separado aguardando readiness e close.
- [x] Checkout aprovado/recusado, validação, identidade, todos os rollbacks e concorrência.
- [x] Relatório administrativo funcional com shape preservado e consultas constantes.
- [x] Exclusão física legítima e desativação legítima preservando todo o financeiro.
- [x] Boot e HTTP reais de todos os 3 endpoints originais e login adicional, erros e autorização.
- [x] Migração/reset controlados testados sem seed destrutivo nem anonimização automática.
- [x] Reauditoria e evidências diretas de execução disponíveis; nenhuma alteração genérica de skill necessária nesta implementação.

Commit das fontes refatoradas: `7366216` (conteúdo funcional validado; logs de integração posteriores identificam a revisão completa).
