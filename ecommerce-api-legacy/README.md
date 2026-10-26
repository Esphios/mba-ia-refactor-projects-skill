# LMS API

API Express/SQLite com checkout e pagamento **simulado**: cartão string iniciado por `4` é aceito; outros prefixos são recusados. Não há cobrança, gateway externo ou envio de email.

## Instalação e execução

Node >=22; execução validada com Node 24.12.0 e npm 11.19.1. Instale pelo lockfile:

```powershell
npm ci
npm test
npm run test:http
```

O SQLite nativo 5.1.7 carregou normalmente no ambiente validado. Não é necessário serviço de banco. O lock conserva as versões originais Express 4.22.1/sqlite3 5.1.7; `npm audit` encontrou 14 advisories (2 critical, 8 high, 1 moderate, 3 low), registrados separadamente no relatório. Não foi aplicada atualização major forçada.

`npm start` inicia na porta 3000, host 127.0.0.1, banco vazio em memória. A configuração é `PORT` (0 aceita porta efêmera), `HOST`, `LMS_DB` e `LMS_DEMO`. Importar `src/app.js` não abre banco nem servidor; `createApplication()` retorna uma aplicação testável e `close()`.

Para uma demonstração que mantenha contas e permita provisionar administrador, use um arquivo **novo**:

```powershell
$env:LMS_DB = Join-Path $PWD 'local.sqlite'
npm run seed:demo
$env:LMS_PASSWORD = Read-Host 'Senha do administrador' -MaskInput
npm run account -- create admin@example.test admin Administrador
Remove-Item Env:LMS_PASSWORD
npm start
```

O seed recusa banco que já contenha cursos/usuários/matrículas/pagamentos; nunca apaga dados. Cria dois cursos e um histórico de demonstração de Leonan com pagamento de 997, **sem senha padrão utilizável**. `LMS_DEMO=1` aplica esse mesmo seed explicitamente no startup e exige banco vazio; retire a opção no próximo boot. Com memória, cada reinício perde os dados e um comando operacional separado não consegue alcançar a conexão do servidor: use `LMS_DB` em arquivo para administrar contas.

## Contas e autenticação

Checkout novo cadastra uma conta comum com senha obrigatória. Checkout de email existente verifica `pwd` contra o hash atual. Senhas usam scrypt com salt aleatório (N=16384, r=8, p=1, chave 64 bytes); entradas excedendo 1024 bytes são recusadas. Formatos truncados/Base64 e plaintext anteriores não autenticam e não recebem fallback.

Com servidor parado, um operador confiável pode criar uma conta ou substituir uma senha. A senha vem de `LMS_PASSWORD`, não de argumento ou arquivo versionado:

```powershell
$env:LMS_DB = Join-Path $PWD 'local.sqlite'
$env:LMS_PASSWORD = Read-Host 'Nova senha' -MaskInput
npm run account -- reset leonan@fullcycle.com.br
Remove-Item Env:LMS_PASSWORD
```

`account create email [user|admin] [nome]` recusa email já existente; `reset email` exige exatamente uma conta e não altera role ou reativa uma conta desativada. Não existe endpoint público de promoção, reset ou login. Basic auth nos endpoints protegidos deve usar transporte protegido fora do loopback; credenciais são verificadas a cada pedido, incluindo active/role atuais do banco.

## Contratos HTTP

| Método/caminho | Contrato |
|---|---|
| POST `/api/checkout` | JSON `usr`, `eml`, `pwd`, `c_id` inteiro positivo, `card` string. Sucesso 200 `{ "msg":"Sucesso", "enrollment_id":2 }`. Entradas inválidas 400; curso ausente/inativo 404; recusa 400 `Pagamento recusado`; senha existente incorreta 401; conta desativada 403. |
| GET `/api/admin/financial-report` | Basic de administrador ativo. 200 array `{course,revenue,students:[{student,paid}]}`. Sem credencial válida 401; role inadequada/conta desativada 403. |
| DELETE `/api/users/:id` | Basic de titular ativo ou administrador ativo. Sem vínculo de matrícula exclui fisicamente; com vínculo desativa e preserva nome/email/matrículas/pagamentos/auditoria. Sucesso 200 `Usuário removido.`. ID inválido 400; sem identidade 401; sem ownership/role 403. |

DELETE inexistente/repetido mantém 200 após autorização administrativa. Titular já desativado recebe 403 na autenticação; a repetição idempotente não contorna o estado atual da conta. Relatório preserva cursos vazios/inativos, `Unknown` para usuário histórico ausente e `paid:0` quando não há pagamento. `paid` mantém valor do pagamento mesmo não PAID, mas receita soma apenas PAID; primeiro pagamento observado por matrícula, sem multiplicação por duplicatas. O original não garantia ordem por usar consultas sem ORDER BY e callbacks: não há nova garantia pública de ordenação.

Todos os participantes do banco usam a fila da conexão. Checkout mantém leitura/decisão/conta/matrícula/pagamento/auditoria/commit na mesma transação; recusa ou qualquer falha reverte a unidade inteira. Exclusão mantém autenticação/ownership/leitura de vínculos/escrita dentro da mesma unidade. Não há cascata financeira nem anonimização automática.

As diferenças deliberadas de segurança, mensagens e efeitos estão na [auditoria aprovada](../reports/audit-project-2.md); comandos e resultados medidos, na [validação](../reports/validation-project-2.md).

## Estrutura e testes

`src/app.js` compõe a aplicação; `server.js` controla boot/readiness/shutdown; `routes/` adapta HTTP; `controllers/` coordena casos; `models/` contém SQL; `services/` possui checkout/exclusão transacionais e simulador; `database/` controla conexão/migração/fila; `security/` verifica hash e identidade; `domain/` contém estados; `http/` mapeia erros. O original tinha três fontes, com quase tudo em AppManager; agora os limites são explícitos.

`npm test` cobre contratos, autorização, Unicode, senhas completas/salt, reset legado, migração aditiva, falhas em cada escrita e COMMIT, dados financeiros ausentes/null/zero e contagem constante de SELECT. `npm run test:http` inicia **seu próprio processo Node** oculto no Windows com porta 0 e SQLite temporário, aguarda JSON de readiness até 10 segundos, verifica os três caminhos com sucessos/negativas/falhas/concorrência e encerra somente seu processo via IPC. A remoção do banco temporário ocorre depois do encerramento confirmado. Não depende de servidor prévio.

## Migração e rollback

O original usa memória, portanto não existe arquivo persistente original a recuperar após shutdown. Para um arquivo legado fornecido explicitamente, pare o serviço, faça cópia integral e configure `LMS_DB`:

```powershell
Copy-Item -LiteralPath $env:LMS_DB -Destination "$($env:LMS_DB).before-mvc"
npm start
```

O boot cria somente tabelas ausentes, adiciona `active` (padrão 1), `role` (padrão user) e índices auxiliares; preserva IDs, credenciais legadas e históricos. Não executa seed sem opção explícita. Usuários legados precisam de reset confiável. Órfãos já existentes permanecem no histórico; não são apagados nem atribuídos a outra pessoa. Não há FK nova que invalide o banco legado.

Para rollback, pare o serviço e restaure a **cópia integral** correspondente ao código anterior; não remova colunas manualmente. Não volte a expor autenticação parcial ou senha padrão em ambiente acessível. Um rollback restaura o estado do backup e perde gravações posteriores: preserve a cópia atual antes e planeje reconciliação. Banco/backup e credenciais não devem ser versionados.
