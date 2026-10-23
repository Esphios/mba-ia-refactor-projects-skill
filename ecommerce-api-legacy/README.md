# E-commerce / LMS API

API Express com checkout simulado, relatório financeiro e ciclo de vida de usuários. Os três endpoints originais continuam disponíveis com autenticação e integridade nos fluxos documentados.

## Execução

Requer Node.js 24 e npm (SQLite 6 exige Node >=20.17). Na pasta deste projeto, em PowerShell:

```powershell
npm ci
$env:AUTH_SECRET = node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
$env:DEMO_SEED = 'true'
$env:DEMO_ADMIN_EMAIL = 'admin@example.test'
$env:DEMO_ADMIN_PASSWORD = 'escolha-uma-senha-unica'
npm start
```

O servidor escuta em `127.0.0.1:3000` somente após validar configuração e concluir schema/seed. `PORT=0` escolhe uma porta disponível. `DB_PATH` tem padrão `:memory:`: os dados desaparecem ao desligar. Um caminho de arquivo permite persistência. `DEMO_SEED` é desativado por padrão e exige as duas credenciais externas; cria administrador e os cursos Clean Architecture (997) e Docker (497) apenas quando o banco ainda não tem tabela de usuários. Não cria a conta legada com senha pública. Um banco existente nunca recebe seed automático. `.env.example` lista opções; exporte-as no shell, pois não há carregador automático de `.env`.

## Contratos HTTP e autorização

| Método / caminho | Acesso e entrada | Resultado |
| --- | --- | --- |
| `POST /api/auth/login` | Público; `{email,password}` | `200 {access_token,token_type:"Bearer",expires_in}`; entrada inválida `400`, credencial incorreta/inativa ou conta legada sem reset `401` |
| `POST /api/checkout` | `{usr,eml,pwd,c_id,card}`; conta nova exige senha 8..256 caracteres; conta existente exige senha correta ou Bearer do próprio titular | `200 {msg:"Sucesso",enrollment_id}`; entrada inválida `400`, identidade ausente/incorreta `401`, curso ausente/inativo `404`, falha de DB `500` |
| `GET /api/admin/financial-report` | Bearer de administrador ativo | `200 [{course,revenue,students:[{student,paid}]}]`; anônimo `401`, usuário comum `403`, falha `500` |
| `DELETE /api/users/:id` | Bearer do titular ou administrador ativo; ID inteiro positivo | `200 {msg,id,action}`; sem relações: `action:"deleted"`; com matrículas: `action:"deactivated"`; inválido `400`, anônimo `401`, outro usuário `403`, ausente `404`, falha `500` |

O simulador aprova cartões numéricos de 12..19 dígitos começando com `4`; outros prefixos retornam `400 "Pagamento recusado"`. Não integra gateway nem faz cobrança real. Campos públicos `usr`, `eml`, `pwd`, `c_id`, `card` permanecem. Nome/email/cartão têm validação de tipo e limite; email é normalizado em minúsculas, `c_id` deve ser inteiro JSON positivo. Falhas de entrada usam `Bad Request`; falhas internas usam `Erro DB`, sem SQL nem dados sensíveis.

O relatório mantém `paid` como valor do pagamento mesmo quando recusado; receita soma apenas status `PAID`. Cursos sem matrículas continuam aparecendo. A ordenação agora é determinística por ID de curso/matrícula. Na base migrada, o primeiro pagamento por ID é usado quando há vários pagamentos históricos por matrícula. Não retorna senhas nem hashes.

Senhas usam scrypt com salt aleatório por conta; tokens HMAC SHA-256 expiram (`TOKEN_TTL_SECONDS=3600`, máximo 86400). Em cada chamada autenticada, identidade/role/estado são recarregados do banco. Uma conta desativada deixa de autenticar imediatamente. Desativação não anonimiza nome/email nem apaga matrículas, pagamentos ou logs. Não há promoção pública a administrador. Os logs de checkout contêm apenas evento, resultado e ID de matrícula.

## Arquitetura e transações

`src/server.js` valida configuração, aguarda `createApplication` e inicia/encerra o servidor. `src/app.js` compõe dependências sem escutar ao ser importado. `routes` registra caminhos e middleware; `controllers` traduz entradas/saídas; `models` contém SQL; `services` coordena identidade, checkout, simulador e retenção. `validation`, `security`, `errors` e `db` isolam preocupações próprias.

Uma instância possui uma conexão SQLite explicitamente fechável. Toda operação passa pela mesma fila: a transação `BEGIN IMMEDIATE` retém a fila até `COMMIT` ou `ROLLBACK`, incluindo os awaits. Leituras também aguardam a fila, evitando participar de uma transação de outra requisição. Cadastro, matrícula, pagamento e auditoria são atômicos. Erro em qualquer escrita reverte todos os registros. O cache global sem consumidor e `totalRevenue` foram removidos.

## Migração controlada e rollback

O projeto original só usava memória. Para uma cópia persistente com schema legado:

1. Pare o servidor e mantenha cópia externa verificada. Nunca rode migração num banco em uso.
2. Defina `DB_PATH` para a cópia e execute `npm run migrate:legacy`. O comando cria `<DB_PATH>.pre-migration.bak` sem sobrescrever backup existente.
3. A migração adiciona role `user`, estado ativo, data de exclusão e flag de reset; conserva IDs, nomes, senhas antigas e todos os valores financeiros. Não promove contas, não apaga dados e falha atomicamente diante de emails duplicados sem tentar mesclá-los.
4. O formato antigo era ambíguo: texto puro ou transformação truncada sem recuperação confiável. Todas as credenciais legadas ficam bloqueadas para login até reset explícito. Para cada titular previamente identificado, defina `RESET_EMAIL`, `RESET_PASSWORD` (8..256 caracteres) e execute `npm run reset:password`. O reset grava scrypt; não reativa conta desativada nem altera privilégios. Remova a senha do ambiente depois.
5. Execute a aplicação e confira totais e acessos. O startup rejeita banco legado ainda não migrado e fecha a conexão sem aceitar requisições.

Rollback: pare o servidor, preserve uma cópia do estado pós-migração, restaure o backup pré-migração e a revisão anterior da aplicação. A restauração desfaz resets posteriores; considere novas operações financeiras antes de fazê-la. Novos schemas têm foreign keys `RESTRICT`; bancos legados mantêm seu histórico, inclusive órfãos preexistentes, sem reparo destrutivo automático. A política do serviço impede novas exclusões que criariam órfãos. O relatório tolera usuário/pagamento histórico ausente.

## Validação reproduzível

```powershell
npm ci
npm test
npm run test:http
npm audit --json
```

`npm test` executa testes node:test, incluindo caracterização dos três contratos no fonte original via `git show 6d1ce62` e VM isolada com SQLite em memória, testes de segurança, falhas induzidas em cada escrita, concorrência, retenção, migração e contagem constante de consultas. Não exige configuração externa. A caracterização requer o histórico Git original.

`npm run test:http` inicia um processo real, cria seu próprio banco temporário/configuração/porta e verifica todos os caminhos (sucesso, negação, entradas ausentes/inválidas, erros, rollback e concorrência), fecha o processo e apaga somente o diretório temporário criado pelo runner. O log omite tokens, senhas e cartões. Não usa dados locais existentes.

Veja [auditoria](../reports/audit-project-2.md), [validação e limitações](../reports/validation-project-2.md) e [evidências HTTP](../reports/evidence/project-2-http.log).
