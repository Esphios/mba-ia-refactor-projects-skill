# Task Manager API

API Flask com 22 pares método/caminho. A refatoração aprovada em 23/10/2026 mantém as rotas, mensagens válidas, serializers específicos e persistência SQLite. Auditoria: [audit-project-3](../reports/audit-project-3.md). Evidências e limitações: [validation-project-3](../reports/validation-project-3.md).

## Estrutura e responsabilidades

- `app.py`: factory, configuração, composição, init-db e erros centralizados; importar não cria schema.
- `routes/`: adaptação HTTP e exigência de identidade/papel.
- `controllers/`: casos de uso de tarefas, usuários, categorias e relatórios.
- `models/`: entidades e `store.py`, fronteira de consultas/transações.
- `services/security.py`: tokens e migração controlada de senha.
- `utils/domain.py`, `validation.py`: regras, datas e limites compartilhados.
- `seed.py`: dados demonstrativos somente para banco explicitamente descartável.

## Preparar e executar (PowerShell)

Python 3.12 foi validado. Em ambiente novo:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
$env:SECRET_KEY = .venv/Scripts/python.exe -c "import secrets; print(secrets.token_hex(32))"
$env:DATABASE_URL = 'sqlite:///' + (Join-Path $PWD 'demo.db').Replace('\', '/')
.venv/Scripts/python.exe -m flask --app app:create_app init-db
.venv/Scripts/python.exe app.py
```

O padrão de bind é `127.0.0.1:5000`, debug desativado. `HOST` e `PORT` configuram o bind. `SECRET_KEY` é obrigatória; use armazenamento de segredos no ambiente de implantação. `TOKEN_MAX_AGE` configura validade em segundos, padrão 3600. Os testes geram suas próprias credenciais e bancos; nenhum segredo real é necessário. A configuração não inicia SMTP; `NotificationService` só envia por transporte explicitamente injetado, simulado nos testes.

## Seed demonstrativo

Com o servidor parado, escolha **outro arquivo descartável** e mantenha a mesma configuração de segredo:

```powershell
.venv/Scripts/python.exe seed.py --database "$PWD/fixture-demo.db" --disposable
```

A aplicação não executa seed automaticamente. O comando recusa banco não vazio; `--replace` autoriza apagar/recriar apenas o banco explicitamente declarado descartável. Todo o conjunto é uma transação. Não use `--disposable` para dados reais. O seed conserva três contas ilustrativas: joao@email.com (admin, senha 1234), maria@email.com (user, abcd), pedro@email.com (manager, pass). Elas servem somente à demonstração local; os hashes são modernos. Para iniciar sobre esse arquivo, ajuste DATABASE_URL para fixture-demo.db. Não exponha essa demonstração publicamente.

## Autenticação e permissões

`POST /users` continua público, com name/email/password e role=user; senha mínima continua quatro caracteres. Apenas admin autenticado pode cadastrar papel privilegiado. `POST /login` aceita email/password e retorna message/user/token, sem password. Use `Authorization: Bearer <token>` nas rotas protegidas.

Usuário ativo lê/altera/exclui suas tarefas, consulta seus próprios dados/tarefas/relatório e altera seu name/email/password. Na criação de tarefa, user_id omitido assume sua identidade; null/outro dono e transferência são recusados. Manager pode visualizar globalmente, atribuir tarefas e manter categorias, mas altera somente seus próprios dados pessoais. Admin pode alterar role/active e excluir usuários com suas tarefas. Leitura de categorias exige autenticação. Relatório global e lista de usuários são manager/admin. Tarefas sem dono ficam para manager/admin. Conta/papel atuais são consultados em cada requisição, sem confiar em papel embutido no token. Token inválido/expirado/ausente: 401; permissão insuficiente/inatividade: 403.

## Migrar sem perder dados

O schema original permanece compatível; init-db cria apenas tabelas ausentes. Não execute seed na base existente. Pare o serviço e faça backup consistente antes de implantação, por exemplo com sqlite3.Connection.backup em um comando administrativo próprio. Valide a restauração em cópia descartável antes de usar o backup como rollback.

Hashes MD5 reconhecidos podem migrar depois de login correto se houver prazo explícito:

```powershell
$env:LEGACY_MD5_CUTOFF = '2026-12-31T23:59:59'
```

O prazo usa UTC sem offset; no instante do corte o login MD5 já é recusado. Sem essa variável, MD5 está desabilitado. Hash moderno nunca recai em verificação MD5. O upgrade persiste na transação do login; conta inativa não é migrada. Depois do corte, contas ainda legadas precisam de redefinição administrativa de senha. Tokens falsos antigos deixam de funcionar; chaves já implantadas devem ser rotacionadas. A escolha do prazo e a redefinição de contas reais são operações administrativas, não executadas pelos testes.

Datas persistidas/HTTP mantêm UTC ingênuo e strings anteriores; a obtenção de UTC usa datetime.now(timezone.utc) com normalização em uma fronteira única. LIKE continua no SQLite, incluindo curingas %/_, Unicode e seu comportamento original de case. Não foram adicionadas paginação, novas regras de cor ou aumento do mínimo de senha.

## Rollback

Guarde código/configuração e backup do banco antes da implantação. Restaure primeiro em ambiente isolado e confira IDs, relações e contagens. Código legado MD5 não autentica hashes já migrados: mantenha o verificador moderno compatível durante rollback ou restaure backup sob plano que reconheça perda de alterações posteriores. Nunca reduza hashes modernos a MD5 nem restaure segredo revogado. Reverter autorização reabre a exposição original. Restauração de banco real exige janela de parada e autorização operacional; a validação desta entrega não toca bases existentes.

## Validar

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe tests/run_http_matrix.py
```

O primeiro comando executa apenas a suíte nova em tests/skill_run; warnings de depreciação são erros. O segundo copia fontes atuais para diretório temporário, cria banco/fixtures/segredo, inicia seu próprio processo sem janela com porta efêmera, verifica os 22 contratos por HTTP real e casos de autorização, e encerra somente seu filho em finally. Nenhum servidor externo ou porta fixa é necessário.

Para comparar com o baseline sanitizado produzido nesta execução:

```powershell
.venv/Scripts/python.exe tests/run_http_matrix.py --baseline ../reports/evidence/skill-run-project-3-baseline.json --output ../reports/evidence/skill-run-project-3-http-reproduced.json
```

A comparação remove password conforme aprovação e normaliza somente token/timestamps identificados. Datas de vencimento, campos, tipos e contagens continuam comparados. As fixtures repetem leitura depois de escrita/exclusão. A [validação do projeto 3](../reports/validation-project-3.md) relaciona os logs RED/GREEN, consultas, versões, hashes e demais evidências. O ambiente utilizado na execução registrada foi `.venv/skill-run-20261023`; o roteiro acima cria um ambiente novo padrão.
