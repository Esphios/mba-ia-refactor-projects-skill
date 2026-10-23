# Task Manager API

API Flask com os 22 métodos/caminhos originais. Models mantêm entidades e acesso a dados; rotas adaptam HTTP; controllers coordenam regras. Categorias possuem blueprint próprio; configuração, autenticação, validação, datas e erros são compartilhados.

## Executar no PowerShell

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
$env:SECRET_KEY = [guid]::NewGuid().ToString() + [guid]::NewGuid().ToString()
$env:DATABASE_URL = 'sqlite:///tasks.db'
.venv/Scripts/python -m flask --app 'app:create_app' init-db
.venv/Scripts/python app.py
```

Servidor local em 127.0.0.1:5000, sem debug. Configure um segredo estável e aleatório no ambiente de produção. O factory não cria nem limpa schema; `init-db` cria tabelas ausentes e não apaga dados. CORS amplo removido; mesma origem por padrão. Para fixtures opcionais de um banco vazio, configure `SEED_ADMIN_PASSWORD` e execute `.venv/Scripts/python seed.py`; banco já populado é recusado. Não use fixtures em produção.

```powershell
.venv/Scripts/python -m pytest tests -q -s
.venv/Scripts/python tests/run_http_matrix.py
```

O segundo comando prepara banco temporário, inicializa processo real em porta livre, executa sucesso dos 22 contratos e encerra o servidor. Nenhum banco existente, cobrança ou e-mail externo é usado. Python 3.12.10 / Flask 3.0.0 / Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.1.6 foram verificados. Dependências efetivas estão no log de versões.

## Identidade e contratos

`POST /users` público cria somente role `user`. `POST /login` aceita email/password e retorna message/user/token; use `Authorization: Bearer <token>`. Senha/hash nunca é retornado. Token é assinado, expira em `TOKEN_MAX_AGE` segundos (padrão 3600), e cada chamada consulta a conta/role/active atual. Token não inclui senha. Trocar SECRET_KEY invalida tokens existentes.

Tarefas (incluindo busca/stats) são do titular, com acesso global para admin. Usuários individuais, alteração/exclusão e relatório por usuário: titular ou admin. Lista de usuários e resumo: admin. Categorias: lista autenticada, escrita admin. Alteração de role/active somente admin. Atribuição de tarefa a outro usuário somente admin. Os erros usam objeto `error`; 401 sem identidade, 403 sem permissão, 404 ausente e 400 entrada inválida.

Novas senhas usam Werkzeug scrypt com salt individual. MD5 é reconhecido somente em hashes legados de 32 caracteres, antes de `LEGACY_MD5_CUTOFF` (padrão `2027-01-01T00:00:00+00:00`); somente login válido de conta ativa persiste upgrade. Após cutoff o usuário precisa redefinição de senha por administrador. Antes de abrir banco real, faça backup offline: copie o SQLite com a aplicação parada, teste o upgrade em uma cópia e mantenha o original. Não reverta hashes scrypt para MD5; rollback usa código compatível com scrypt ou backup anterior, com perda dos writes posteriores explicitamente avaliada.

Datas legadas ingênuas representam UTC. O helper central converte datas aware para UTC e remove timezone na fronteira de armazenamento, mantendo respostas `YYYY-MM-DD HH:MM:SS`. Data de vencimento aceita `YYYY-MM-DD`; task concluída/cancelada não fica atrasada; igualdade com agora não é atraso.

Excluir usuário apaga suas tarefas em uma transação; excluir categoria desvincula tarefas, preservando-as. Validação completa precede mutações e falhas de persistência causam rollback. Listagens usam eager loading; queries medidas com 1 e 21 tarefas permanecem constantes. Paginação não fazia parte da implementação original; listagens continuam retornando arrays completos.

## SMTP

Nenhuma rota envia e-mail. O serviço opcional fica desabilitado por padrão; somente `SMTP_ENABLED=true` habilita transporte, usando `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASSWORD`. Nunca grave credenciais no código. Testes usam transporte injetado mock, inclusive no caminho habilitado.

## Skill e evidência

Pacote portátil em `.agents/skills/refactor-arch`, idêntico ao canônico. Para auditar no Codex a partir deste diretório: `$refactor-arch` e solicite análise das fases 1/2. A skill normalmente exige aprovação antes de escrever; nesta execução o usuário dispensou as pausas explicitamente.

[Auditoria](../reports/audit-project-3.md) e [validação](../reports/validation-project-3.md) registram os achados, alterações de contrato, comandos e logs reais. O servidor Flask é adequado para validação local; produção deve usar servidor WSGI configurado pelo operador. Testes não constituem auditoria externa de segurança nem teste de carga.
