# Project 1 characterization baseline

Date: 2026-10-22. Source revision before transformation:
`6d1ce6248c3e956801010a89d8bdaab48029bf30`.

## Isolated environment

```powershell
python -m venv code-smells-project/.venv-refactor
code-smells-project/.venv-refactor/Scripts/python.exe -m pip install `
  -r code-smells-project/requirements.txt pytest==8.4.2
code-smells-project/.venv-refactor/Scripts/python.exe -m pytest -q `
  code-smells-project/tests
```

Every test uses a unique SQLite database under pytest's temporary directory.
No repository database existed or was opened, and no destructive project seed
command was run. The test fixture invokes only the application's existing schema
bootstrap against that disposable path.

Runtime and installed versions are in [project-1-runtime.txt](project-1-runtime.txt)
and [project-1-dependencies.txt](project-1-dependencies.txt).

## Contract coverage

`tests/test_http_contracts.py` exercises all 19 explicit method/path pairs:

1. `GET /`
2. `GET /produtos`
3. `GET /produtos/busca`
4. `GET /produtos/<id>`
5. `POST /produtos`
6. `PUT /produtos/<id>`
7. `DELETE /produtos/<id>`
8. `GET /usuarios`
9. `GET /usuarios/<id>`
10. `POST /usuarios`
11. `POST /login`
12. `POST /pedidos`
13. `GET /pedidos`
14. `GET /pedidos/usuario/<usuario_id>`
15. `PUT /pedidos/<pedido_id>/status`
16. `GET /relatorios/vendas`
17. `GET /health`
18. `POST /admin/reset-db`
19. `POST /admin/query`

`tests/test_security_and_integrity.py` adds nonpositive/duplicate quantity,
rollback, restock, legacy-password upgrade, tampered/expired token, query count
and discount-boundary cases.

## Pre-refactoring result

Command exit: 1. Result: **9 passed, 23 failed, 0 errors**. The failures reproduce
the approved gaps rather than setup defects: missing 400/401/403/404/409 behavior,
password/secret exposure, plaintext password storage, absent tokens, incomplete
rollback/restock, duplicate-line overselling and seven SELECTs for three one-item
orders. Full output: [project-1-baseline-pytest.txt](project-1-baseline-pytest.txt).

The passing cases characterize current public success behavior and the unchanged
discount thresholds. This red baseline is the gate before production edits.
