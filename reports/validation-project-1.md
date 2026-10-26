# Validação — code-smells-project

Execução da Fase 3 de `refactor-arch` em 23/10/2026. A [auditoria](audit-project-1.md),
seus hashes e a aprovação **“Aprovo o escopo completo apresentado”** foram
persistidos antes das fontes.

## Resultado medido

- Python 3.12.10, Flask 3.1.1, Flask-Cors 5.0.1, Werkzeug 3.1.9,
  itsdangerous 2.2.0 e SQLite 3.49.1 medidos no ambiente isolado.
- **66 testes passaram**, sem skip, em `python -m pytest -q`.
- **19 métodos/caminhos e 40 casos HTTP** passaram em processos reais, portas
  efêmeras e banco descartável; os dois filhos pararam e o diretório foi removido.
- Quatro fontes originais deram lugar a factory/rotas/controllers/models/services,
  configuração, autenticação, validadores e serializers explícitos.
- Nenhum banco existente, e-mail, SMS ou serviço externo foi acessado.

Evidências: [ambiente e hashes](evidence/skill-run-project-1-environment.json),
[RED original](evidence/skill-run-project-1-red.log),
[GREEN final](evidence/skill-run-project-1-final-pytest.log) e
[HTTP real](evidence/skill-run-project-1-http.json).

## Achados e contratos

| Grupo | Transformação e verificação |
| --- | --- |
| F01/F12/F13 | SQL de domínio parametrizado; tipos, bool, NaN/infinito, IDs, quantidades e JSON validados; erros internos não vazam detalhes. Apóstrofos, Unicode e `%`/`_` de LIKE cobertos. |
| F02/F03/F04/F05 | Senha/hash removidos das respostas; segredo externo e health saneado; scrypt com salt, janela explícita de upgrade plaintext e sem fallback moderno; Bearer expirável e papel/atividade atuais. Matriz testa 401, 403, proprietário e admin, além do sucesso. |
| F06/F07/F10 | Conexão por contexto e teardown; checkout com BEGIN IMMEDIATE, demanda cumulativa, leitura/decisão/escrita e rollback; concorrência e falhas intermediárias testadas. Listagens usam número constante de SELECTs para 1/20 pedidos. |
| F08/F11/F14 | Routes finas, controller e modelos por domínio; validação/serialização compartilhada; factory, init e seed demonstrativo explícitos. |
| F09/F15/F16 | Debug opt-in, host/porta configuráveis, valores de domínio nomeados e imports comprovadamente mortos removidos. |

Todos os **16 achados** foram tratados: 3 CRITICAL, 6 HIGH, 5 MEDIUM e 2 LOW.
As diferenças aprovadas estão nos contratos de autenticação, remoção de senha e
segredo, validação de entradas e inicialização explícita.

As semânticas preservadas incluem exclusão física de produto; status de pedido
inexistente ainda 200; nenhum ciclo novo de status; cancelamento não repõe estoque;
pedidos cancelados contam receita; itens repetidos continuam linhas separadas após
validação cumulativa; sem nova unicidade de e-mail/FK. O console SQL administrativo
continua arbitrário e funcional, inclusive escrita e DDL, protegido por admin.

## Ciclos RED/GREEN e revisão

O baseline original passou nos 19 contratos legítimos. A primeira suíte de
segurança/regressão produziu 37 falhas e 3 passes. Depois da implementação, revisão
de contrato encontrou diferenças de envelope para JSON `{}` em login/query/status,
erro de health e nome `NULL` versus produto ausente; cada caso recebeu teste antes
da correção. O runner HTTP também reproduziu uma conexão SQLite própria impedindo
cleanup no Windows; [RED](evidence/skill-run-project-1-cleanup-red.log) e
[GREEN](evidence/skill-run-project-1-cleanup-green.log) registram o fechamento.

A revisão independente seguinte encontrou três regressões de bases/entradas
permitidas pelo original: segunda conta com e-mail duplicado não autenticava;
inserção concorrente entre duas consultas podia causar `KeyError` na listagem;
IDs/preço inteiros além de 64 bits chegavam ao bind SQLite e viravam 500. O
[RED](evidence/skill-run-project-1-review-red.log) reproduziu os casos. A correção
percorre contas até a senha correspondente, lê pedidos/itens em um único JOIN
consistente, evita bind de IDs fora da faixa e preserva preço finito como REAL.
[GREEN](evidence/skill-run-project-1-review-green.log): 23 testes focados.

## Migração, rollback e limites

O [README do projeto](../code-smells-project/README.md) documenta init, provisão,
seed, backup, cutoff e rollback. Nenhuma base real foi migrada. Texto puro legado
só migra após login correto antes de `SHOP_LEGACY_PASSWORD_CUTOFF`; sem cutoff é
recusado e hash moderno nunca tenta fallback. Reverter código exige manter suporte
aos hashes modernos ou restaurar backup, com perda de escritas avaliada pelo
operador. Esta validação não é load test nem valida implantação/TLS.

Comandos, dentro do projeto:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python tests/run_http_matrix.py
```
