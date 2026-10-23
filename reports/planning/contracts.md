# Inventário estático de contratos e autorização

Revisão examinada: `6d1ce6248c3e956801010a89d8bdaab48029bf30`.
Este inventário foi obtido por leitura de `app.py`, blueprints e `AppManager.js`;
nenhum servidor, seed ou banco foi executado. Status de erro incluem pelo menos
entrada inválida e recurso ausente quando aplicáveis. A classificação de acesso é
a política proposta para confirmação na Fase 2, não uma alegação sobre a proteção
do código legado.

## Projeto 1 — code-smells-project (19 pares)

| Método e caminho | Entrada / efeito e resposta de sucesso | Fixture planejada | Acesso / propriedade | Testes positivos e negativos |
| --- | --- | --- | --- | --- |
| GET `/` | Sem entrada; catálogo da API, 200 | nenhuma | público / n/a | 200; método não permitido |
| GET `/produtos` | Lista produtos ativos, 200 | produtos ativos/inativo | público / n/a | lista; vazio |
| GET `/produtos/busca` | `q`, `categoria`, `preco_min`, `preco_max`; lista, 200 | produtos variados | público / n/a | filtros; número inválido |
| GET `/produtos/<id>` | ID; produto, 200 | produto existente | público / n/a | existente; 404 |
| POST `/produtos` | JSON de produto; cria e retorna ID, 201 | admin e categorias | admin / n/a | válido/autorizado; 400 e 401/403 |
| PUT `/produtos/<id>` | ID + JSON completo; atualiza, 200 | produto e admin | admin / n/a | válido/autorizado; 400, 404 e 401/403 |
| DELETE `/produtos/<id>` | ID; desativa/exclui, 200 | produto e admin | admin / n/a | existente/autorizado; 404 e 401/403 |
| GET `/usuarios` | Lista usuários sem segredo, 200 | usuários | admin / n/a | autorizado; 401/403 |
| GET `/usuarios/<id>` | ID; usuário sem segredo, 200 | titular, terceiro e admin | autenticado / titular ou admin | titular/admin; 404 e terceiro negado |
| POST `/usuarios` | nome, email, senha; cria ID, 201 | email livre | público / n/a | válido; corpo inválido/conflito |
| POST `/login` | email e senha; usuário sem segredo, 200 | credencial legada/nova | público / n/a | ambas válidas; credencial inválida/injeção |
| POST `/pedidos` | usuário e itens; pedido/total, 201 | usuário, estoque e itens | autenticado / titular | sucesso; quantidade/estoque inválido e rollback |
| GET `/pedidos` | Lista pedidos, 200 | vários pedidos/itens | admin / n/a | autorizado; 401/403; limite de queries |
| GET `/pedidos/usuario/<usuario_id>` | Lista do usuário, 200 | titular, terceiro e pedidos | autenticado / titular ou admin | titular/admin; terceiro negado |
| PUT `/pedidos/<pedido_id>/status` | status; atualiza, 200 | pedido e admin | admin / n/a | transições aprovadas; status inválido/negação |
| GET `/relatorios/vendas` | Totais de vendas, 200 | pedidos em estados variados | admin / n/a | autorizado; 401/403; agregação correta |
| GET `/health` | Saúde sanitizada, 200 | banco temporário | público / n/a | saudável; falha do banco sem segredo |
| POST `/admin/reset-db` | Sem corpo; limpa banco descartável, 200 | banco temporário + credencial | admin / n/a | autorizado funcional; 401/403 |
| POST `/admin/query` | SQL administrativo; dados/mensagem, 200 | banco temporário + credencial | admin / n/a | SELECT autorizado; 400, 401/403 e erro sanitizado |

## Projeto 2 — ecommerce-api-legacy (3 pares)

| Método e caminho | Entrada / efeito e resposta de sucesso | Fixture planejada | Acesso / propriedade | Testes positivos e negativos |
| --- | --- | --- | --- | --- |
| POST `/api/checkout` | `usr`, `eml`, `pwd`, `c_id`, `card`; matrícula/pagamento, 200 | curso, usuário novo e simulador | público para conta nova; senha ou Bearer titular para existente / comprador | aprovação; recusa, curso inválido, corpo inválido, identidade e rollback |
| GET `/api/admin/financial-report` | Sem corpo; receita e vendas, 200 | matrículas/pagamentos | admin / n/a | autorizado; 401/403; múltiplos registros sem N+1 |
| DELETE `/api/users/:id` | ID; política de exclusão confirmada, 200 | usuário sem vínculo e com histórico | autenticado / titular ou admin | remoção sem vínculo; desativação com histórico; 404, 401/403 |

Decisão obrigatória da Fase 2: escolher entre desativação/retenção, bloqueio por
vínculos ou remoção transacional para usuários do LMS. O padrão proposto é não
apagar histórico financeiro automaticamente e manter ao menos um fluxo legítimo
de exclusão verificável.

## Projeto 3 — task-manager-api (22 pares)

| Método e caminho | Entrada / efeito e resposta de sucesso | Fixture planejada | Acesso / propriedade | Testes positivos e negativos |
| --- | --- | --- | --- | --- |
| GET `/` | Catálogo, 200 | nenhuma | público / n/a | 200; método inválido |
| GET `/health` | Saúde sanitizada, 200 | banco temporário | público / n/a | saudável; falha sanitizada |
| GET `/tasks` | filtros/paginação; lista, 200 | tarefas variadas | autenticado / próprias; admin todas | titular/admin; token ausente/terceiro |
| GET `/tasks/<id>` | tarefa, 200 | titular, terceiro e tarefa | autenticado / titular ou admin | titular/admin; 404 e terceiro negado |
| POST `/tasks` | dados da tarefa; cria, 201 | usuário/categoria | autenticado / titular | válido; entrada, categoria e identidade inválidas |
| PUT `/tasks/<id>` | alterações; atualiza, 200 | tarefa do titular/terceiro | autenticado / titular ou admin | titular/admin; 400, 404 e terceiro negado |
| DELETE `/tasks/<id>` | remove, 200 | tarefa do titular/terceiro | autenticado / titular ou admin | titular/admin; 404 e terceiro negado |
| GET `/tasks/search` | consulta; lista, 200 | títulos/tags variados | autenticado / próprias; admin todas | correspondência; token ausente |
| GET `/tasks/stats` | estatísticas, 200 | estados/prioridades variados | autenticado / próprias; admin todas | agregação; token ausente |
| GET `/users` | lista sem hash, 200 | usuários | admin / n/a | autorizado; 401/403 |
| GET `/users/<id>` | usuário sem hash, 200 | titular, terceiro e admin | autenticado / titular ou admin | titular/admin; 404 e terceiro negado |
| POST `/users` | nome/email/senha; usuário sem hash, 201 | email livre | público / n/a | role user; role privilegiada negada/conflito |
| PUT `/users/<id>` | alterações; usuário sem hash, 200 | titular, terceiro e admin | autenticado / titular ou admin | titular; terceiro negado; promoção só admin |
| DELETE `/users/<id>` | remove usuário/tarefas, 200 | titular, terceiro e admin | autenticado / titular ou admin | titular/admin; 404 e terceiro negado |
| GET `/users/<id>/tasks` | tarefas do usuário, 200 | titular, terceiro e admin | autenticado / titular ou admin | titular/admin; terceiro negado |
| POST `/login` | email/senha; token expirável, 200 | hash legado/novo e usuário inativo | público / n/a | legado/novo; inválido, inativo, token adulterado/expirado |
| GET `/reports/summary` | resumo, 200 | tarefas/usuários/categorias | admin / n/a | autorizado/agregação; 401/403 |
| GET `/reports/user/<id>` | relatório do usuário, 200 | titular, terceiro e admin | autenticado / titular ou admin | titular/admin; 404 e terceiro negado |
| GET `/categories` | lista, 200 | categorias | autenticado / n/a | autorizado; token ausente |
| POST `/categories` | dados; cria, 201 | categoria livre | admin / n/a | autorizado; 400 e 401/403 |
| PUT `/categories/<id>` | alterações; atualiza, 200 | categoria e admin | admin / n/a | autorizado; 404 e 401/403 |
| DELETE `/categories/<id>` | remove, 200 | categoria livre/vinculada | admin / n/a | livre; 404, 401/403 e vínculo tratado |

## Diferenças de contrato a apresentar na Fase 2

- Remover senha, hash, segredo e detalhes internos de respostas e logs.
- Exigir identidade verificável, expiração e autorização onde a matriz indica.
- Restringir as duas ferramentas administrativas da loja sem remover seus fluxos autorizados.
- Tornar pedido e checkout atômicos e rejeitar quantidade/entrada inválida.
- Definir com o usuário a retenção financeira na exclusão do LMS.
- Preservar métodos, caminhos, chaves legítimas e resultados de negócio fora das correções aprovadas.


## Decisões finais da implementação

A instrução “ignore as aprovações por enquanto. continue até o fim.” autorizou os
planos apresentados e eliminou novas pausas nesta execução. O LMS adiciona
POST /api/auth/login (público, email/password, token expiráveis), preservando os
três pares originais. DELETE admite titular/admin: remove fisicamente usuário
sem vínculos, desativa quando há matrícula/pagamento, mantendo todo o histórico e
sem anonimização automática. Tokens da conta desativada são negados. O checkout
com email existente exige senha ou identidade Bearer correspondente.

Os três relatórios validation-project-N vinculam sucesso autorizado, negações,
fixtures e testes de cada política. No projeto 1 admin executa SQL arbitrário/reset
em banco descartável. No projeto3 tasks são filtradas por proprietário antes dos
filtros de busca SQL LIKE originais; parâmetros preservam wildcards legítimos.
Todas as diferenças de segurança estão nas auditorias iniciais, e as descobertas
posteriores de compatibilidade foram corrigidas sem descartar endpoints.
