# code-smells-project

API de loja em Python/Flask com SQLite. A refatoração foi gerada do original pela skill local `refactor-arch`, após a aprovação humana de F01–F16. Auditoria: [audit-project-1.md](../reports/audit-project-1.md). Evidências e limitações: [validation-project-1.md](../reports/validation-project-1.md).

## Instalação e execução

Python 3.12 foi validado nesta execução. No PowerShell, dentro deste diretório:

```powershell
python -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements.txt -c requirements-lock.txt
$env:SHOP_SECRET_KEY = (& .venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(48))")
$env:SHOP_DATABASE = (Join-Path $PWD 'loja.db')
& .venv/Scripts/python.exe -m flask --app app:create_app init-db
& .venv/Scripts/python.exe -m flask --app app:create_app create-admin
& .venv/Scripts/python.exe app.py
```

`create-admin` solicita email e senha (oculta, com confirmação); não há conta ou senha padrão. Guarde a chave em configuração persistente do ambiente de execução; trocá-la invalida tokens existentes. `init-db` cria somente tabelas ausentes e preserva dados. Importar a aplicação não abre o banco nem executa seed. O primeiro boot exige esquema inicializado e uma chave externa.

O servidor de desenvolvimento usa `127.0.0.1:5000`, sem debug/reloader. `SHOP_HOST` e `SHOP_PORT` configuram endereço/porta. `SHOP_DEBUG=1` habilita explicitamente o modo de desenvolvimento. O objeto WSGI pode ser composto por `create_app()` no servidor escolhido para implantação.

Catálogo demonstrativo é opcional, apenas em banco descartável vazio já inicializado:

```powershell
& .venv/Scripts/python.exe -m flask --app app:create_app seed-demo --disposable
```

O comando insere dez produtos e nenhuma conta; recusa banco não vazio. `get_db()` nunca repopula dados, inclusive após reset/reinício.

## HTTP e acesso

Os 19 métodos/caminhos originais constam da auditoria. `POST /login` recebe `email`/`senha`, preserva os dados públicos do usuário e adiciona `token` e `expires_in` no envelope superior. Use `Authorization: Bearer <token>`. Expiração padrão: 3600 segundos; uma composição pode configurar `TOKEN_TTL` inteiro positivo. Identidade e papel são recarregados do banco em cada request.

| Acesso | Rotas |
|---|---|
| Público | `GET /`, leituras de produtos/busca, `POST /usuarios`, `POST /login`, `GET /health` |
| Administrador | Escritas de produtos, `GET /usuarios`, `GET /pedidos`, alteração de status, relatório, reset e console SQL |
| Proprietário ou administrador | `GET /usuarios/<id>`, `GET /pedidos/usuario/<usuario_id>` |
| Autenticado | `POST /pedidos`: próprio `usuario_id`, ou outro usuário se administrador |

Ausência/credencial inválida retorna 401; falta de permissão retorna 403. Usuários nunca expõem `senha`/hash. Health mantém contagens e informações não sensíveis, remove `secret_key` e mostra debug real. Erros internos retornam mensagem genérica; o envelope especial de health é preservado.

`POST /admin/query` continua aceitando SQL arbitrário, inclusive DDL/escrita/PRAGMA, sob administração verificada. Essa é uma fronteira de confiança excepcional, não uma API de consulta pública. SELECT mantém `dados`; os demais comandos mantêm a mensagem original. `POST /admin/reset-db` continua apagando as quatro tabelas de domínio. Nenhum teste opera sobre seu banco real.

POST e PUT de produto compartilham limites/categorias. Preço é finito e não negativo; estoque é inteiro não negativo; booleanos não são números válidos. Pedido exige IDs/quantidades inteiros positivos e usuário existente. Estoque acumulado de itens repetidos é validado dentro da mesma transação que lê preço e grava pedido/itens/baixas. Erros fazem rollback completo; pedidos concorrentes não vendem o mesmo estoque.

Semânticas preservadas: SQLite LIKE (inclusive curingas e diferença Unicode de case), filtros zero ignorados como no original, categoria/descrição padrão, datas, desconto com limiares estritos e arredondamento, relatório incluindo cancelados, exclusão física e produto ausente como `Desconhecido`. Produto existente com nome NULL permanece NULL. Status inexistente ainda responde 200; cancelar não repõe estoque. Não foram criadas transições, unicidade de email ou foreign keys. Email/SMS/push continuam simulações locais, sem serviço externo.

## Migração de banco existente

Nenhum banco existente foi migrado nesta execução. Pare os processos que usam a base, escolha o caminho absoluto e faça backup verificável antes de qualquer alteração. O exemplo abaixo abre a origem em modo somente leitura e se recusa a substituir um backup:

```powershell
& .venv/Scripts/python.exe -c "import os, sqlite3; from pathlib import Path; p=Path(os.environ['SHOP_DATABASE']).resolve(); b=p.with_suffix('.pre-mvc.sqlite'); assert p.is_file() and not b.exists(); src=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True); dst=sqlite3.connect(b); src.backup(dst); assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; dst.close(); src.close(); print(b)"
```

Ensaie em cópia desse backup. `init-db` é idempotente e não converte datas, IDs ou relações. Inconsistências legadas devem ser avaliadas separadamente; não existe limpeza automática nem seed de migração.

Para uma janela explícita de transição de senhas em texto puro, configure `SHOP_LEGACY_PASSWORD_CUTOFF` com data/hora ISO8601 e fuso, escolhida pela operação (por exemplo, `2026-11-30T23:59:59+00:00`). Sem configuração, login legado fica desabilitado. Antes do cutoff, a senha correta promove a conta para scrypt com salt e persiste o hash na transação de login. Na data exata do cutoff e depois dela, texto puro é recusado; hashes modernos continuam funcionando. Nunca há fallback após hash moderno falhar. As contas que não migraram precisam de redefinição administrada fora deste escopo. Credenciais conhecidas do seed antigo e a chave antiga precisam ser rotacionadas; removê-las do código não as apaga da base.

Rollback deve ocorrer com processos parados: use código que entenda os hashes modernos ou restaure o backup verificado. O código original não autentica hashes novos. Restaurar backup perde as escritas posteriores; avalie essa perda antes de executar. Não use reset para migrar ou voltar versão.

## Estrutura e validação

Antes: quatro arquivos com rotas/SQL/validação/orquestração cruzados e conexão global. Depois:

```text
app.py                  factory, configuração e erros
routes/                 HTTP, entrada/saída e proteção de acesso
controllers/shop.py     decisões dos casos de uso, dependências injetáveis
models/                 SQL parametrizado de produtos/usuários/pedidos/sistema
services/checkout.py    coordenação transacional entre modelos
database.py             conexão por contexto, teardown, transações e CLI
auth.py                 hash legado, assinatura, expiração e identidade atual
validators.py           regras de entrada
serializers.py          campos públicos explícitos
domain.py               categorias/status/faixas e cálculo de relatório
tests/                  baseline, segurança, regressões e HTTP real
```

A suíte usa apenas bancos descartáveis e relógios controlados para cutoff/expiração:

```powershell
& .venv/Scripts/python.exe -m pip install -r requirements-dev.txt
$env:PYTHONUTF8 = '1'
& .venv/Scripts/python.exe -m pytest -q
& .venv/Scripts/python.exe tests/run_http_matrix.py
```

O runner HTTP inicia processos Python próprios em portas atribuídas pelo sistema, cria credenciais e banco descartáveis, valida sucesso autorizado e negações, encerra somente esses processos e verifica remoção dos arquivos. Não depende de servidor externo, chave do usuário ou porta fixa. `--output <arquivo.json>` salva resultado sanitizado opcional. O lock registra as versões medidas; não inclui ambientes virtuais, banco real nem credenciais.
