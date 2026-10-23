# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
export SECRET_KEY='troque-por-um-segredo-forte'
export DATABASE='loja.db'
flask --app app init-db
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`, sem modo debug. O esquema é criado
explicitamente por `flask --app app init-db`; o boot de produção não cria nem
popula o banco implicitamente.

Dados de demonstração são opcionais. Defina `DEMO_ADMIN_PASSWORD`,
`DEMO_CUSTOMER_PASSWORD` e `DEMO_SECOND_CUSTOMER_PASSWORD`, depois execute
`flask --app app seed-demo`. As senhas não possuem valores padrão no código.

## Testes

```bash
pip install -r requirements-dev.txt
pytest -q
```

Os testes usam um banco SQLite temporário. `tests/run_http_matrix.py` valida os 19
pares método/caminho contra um processo real já inicializado.

## Estrutura

- `routes/`: métodos, caminhos e guardas de acesso;
- `controllers/`: adaptação HTTP e decisões de caso de uso;
- `services/`: transações e regras que coordenam modelos;
- `models/`: consultas parametrizadas e serialização;
- `database.py`, `config.py`, `auth.py` e `errors.py`: infraestrutura comum.

## Migração e rollback

Faça backup antes de abrir um banco existente e valide primeiro uma cópia. O
login aceita senhas legadas em texto somente até `LEGACY_PASSWORD_CUTOFF`
(padrão: `2027-01-01T00:00:00+00:00`), atualizando para scrypt após autenticação
válida. Depois desse prazo, contas ainda legadas exigem redefinição administrativa
controlada; não existe endpoint público de reset. Senhas novas já usam scrypt.
O seed opcional cria exemplos legados exclusivamente para demonstrar o upgrade;
não use credenciais de demonstração em produção. `.env.example` lista as opções.

Rollback exige restaurar o backup do banco junto do código correspondente. O
código legado que compara texto não autentica hashes scrypt; não converta hashes
de volta a texto. Rotacionar `SECRET_KEY` invalida os tokens emitidos.
