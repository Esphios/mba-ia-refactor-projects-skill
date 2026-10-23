# Avaliação da skill refactor-arch

## Descoberta e fases 1/2 com GPT-5.6 — 22/10/2026

Estado: **concluído em modo somente leitura**.

- Codex: `codex-cli 0.157.0`, override `-m gpt-5.6-sol`.
- Pacote canônico SHA256:
  `1848a52ef70992701552e275e4b3d998d83e94810a3c2e6cae05317e41d3bb57`.
- Descoberta a partir de `code-smells-project`: a saída confirmou o caminho
  `.agents/skills/refactor-arch/SKILL.md`, as fases análise, auditoria/gate e
  transformação aprovada, e declarou que não houve auditoria nem escrita.
  [Resposta completa](evidence/discovery-project-1-gpt-5.6-response.md),
  [eventos](evidence/discovery-project-1-gpt-5.6-events.jsonl) e
  [stderr](evidence/discovery-project-1-gpt-5.6-stderr.txt).
- Conferência do pacote: frontmatter `name`/`description`, entrada pelo diretório
  atual ou caminho fornecido, destino de relatório opcional, três fases, aprovação
  humana explícita e limite de três ciclos estão presentes no `SKILL.md`.
- Entrada da descoberta: `Use $refactor-arch. This is a discovery-only check: ...`
  seguida das restrições de não auditar, escrever, instalar, iniciar processos ou
  alterar Git. A resposta observada identificou corretamente o pacote e o gate.

A execução completa das fases 1/2 usou uma cópia descartável criada por `git
archive` da revisão original
`6d1ce6248c3e956801010a89d8bdaab48029bf30`, acrescida somente do pacote atual.
README raiz, OpenSpec, relatórios, gabarito manual e `docs/refactor-arch` não foram
incluídos. A cópia foi commitada localmente como
`f5ebe7fd3a31a8b03d64a3fa71175c2d4b20262d`; seu tree hash antes e depois foi
`b07038d25fef2f12ad1b9485b37982955d782808`.

A entrada solicitou análise e auditoria completas, contratos, plano MVC,
dependências, diferenças de contrato, migração/rollback e gate, proibindo escrita,
instalação, boot, banco, seed e Fase 3. O resultado observado:

- reconheceu Python/Flask, e-commerce e SQLite direto;
- contou exatamente quatro fontes Python, separando metadados e a própria skill;
- inventariou os 19 pares método/caminho;
- registrou 15 findings: 5 CRITICAL, 4 HIGH, 4 MEDIUM e 2 LOW após
  alinhar AUD-003, AUD-004 e AUD-005 à rubrica explícita do enunciado;
- preservou o console SQL arbitrário como função administrativa protegida;
- apresentou todas as diferenças de contrato, dependências, migração e rollback;
- pediu aprovação explícita e parou antes da Fase 3;
- correspondeu aos cinco achados manuais: P1-01/AUD-001,
  P1-02/AUD-010, P1-03/AUD-011, P1-04/AUD-014 e P1-05/AUD-015.

Após a execução, `git status --porcelain` retornou zero entradas, os diffs staged
e unstaged tiveram exit code 0, e revisão/tree permaneceram idênticos. A saída
gerada originalmente teve SHA256
`e9c9a4ebd1c3c3fda46f02c15f9d467fec71f57c5b096781524c6ce826884d82`.
A [auditoria corrigida após revisão humana](evidence/audit-project-1-phase-1-2-gpt-5.6.md)
tem SHA256 `2c711bdcdcf93769ee2dd6519fa20707f85baf4b63193c36b5a235c6df59ebd6`;
ela reclassifica AUD-003, AUD-004 e AUD-005 como CRITICAL segundo a rubrica, sem
alterar evidências, escopo ou diferenças de contrato. Os eventos preservam a saída
original completa. Os [eventos JSONL](evidence/audit-project-1-phase-1-2-gpt-5.6-events.jsonl)
têm SHA256 `4b282e3e51c05a49ac3f9483a636c9ea5545c8266df4fe5466df05976a371c7b`.

### Confirmação humana

Após receber o relatório completo e as diferenças de contrato, o usuário solicitou
dois ajustes: alinhar três severidades à rubrica e identificar textos históricos
superados. A resposta encerrou com “uma vez ajustados, pode continuar”. Como os
ajustes não mudaram findings, plano, dependências ou contratos propostos, essa
resposta registra aprovação condicional de todos os 15 findings e diferenças de
contrato, efetivada após as correções acima em 22/10/2026. O escopo aprovado inclui
autorização, migração de senhas, transições de pedidos, bloqueio da exclusão de
produto referenciado e manutenção do console SQL arbitrário para administradores.

## Tentativa de descoberta — 22/10/2026 (histórico superado)

Este registro preserva a primeira tentativa para rastreabilidade. Seu estado foi
superado pela execução bem-sucedida com GPT-5.6 registrada acima. Naquele momento,
ela foi bloqueada antes da execução do modelo, não comprovou descoberta, leitura
da skill ou auditoria, e as tarefas 2.1 e 3.1 ainda permaneciam abertas.

- Codex: `codex-cli 0.157.0`.
- Diretório: `code-smells-project` neste repositório, revisão-base
  `6d1ce6248c3e956801010a89d8bdaab48029bf30`; fontes das aplicações intactas.
- Pacote canônico SHA256:
  `1848a52ef70992701552e275e4b3d998d83e94810a3c2e6cae05317e41d3bb57`.
  Manifesto e algoritmo em
  [preparation-checks-2026-10-22.txt](evidence/preparation-checks-2026-10-22.txt).
- Comando: entrada abaixo via stdin para
  `codex exec --sandbox read-only --ephemeral --json -C code-smells-project -o <registro-temporário>/discovery-response.md -`.
- Entrada literal:

```text
Use $refactor-arch. This is a discovery-only check: report whether this skill is available in your discovered skills, read its SKILL.md, list its three phases and approval gate, and stop. Do not audit sources, write files, install dependencies, start processes, or run git-changing commands. Report the resolved skill path.
```

- Resultado: exit code 1; HTTP 400: `The 'gpt-6.1-sol' model is not supported
  when using Codex with a ChatGPT account.` Nenhuma resposta final foi produzida.
- Evidências: [eventos JSONL](evidence/discovery-project-1-failed-2026-10-22.jsonl)
  e [stderr](evidence/discovery-project-1-failed-2026-10-22.stderr.txt).
- Contexto: sessão efêmera no projeto real, sujeita a instruções pessoais e
  ancestrais. Não é a avaliação independente com cópia limpa da tarefa 3.1.
- Próximo passo registrado naquele momento: definir modelo compatível para
  override local e repetir a avaliação. Isso foi concluído posteriormente com
  `gpt-5.6-sol`, sem alterar configuração pessoal.

## Verificações preparatórias — 22/10/2026

O playbook anterior tinha apenas um par Python completo e um exemplo JavaScript
cujo depois delegava a implementação a um comentário. A checagem inicial das doze
famílias identificáveis falhou. Agora há doze pares concretos; os 24 blocos passaram
por `ast.parse` ou `node --check`. Exercícios funcionais cobriram SQL parametrizado,
rollback, contagem de queries, validação, limiares, fronteiras MVC, guarda
administrativa e mapeamento de entrada. Os outros exemplos foram conferidos por
leitura e sintaxe; testes de integração e avaliação comportamental seguem pendentes.

Os links locais do pacote resolvem. `git check-ignore --no-index` confirmou os
três destinos de pacote, `.env.example` e workflow CI como visíveis, mantendo
ambientes, bancos, segredos e instruções locais ignorados. A exceção para workflows
neutraliza a regra preexistente `/.github/` em `.git/info/exclude`. Resultados e
hashes estão no log acima. `quick_validate.py` da skill `skill-creator` não executou
por falta de PyYAML no Python global; validação YAML formal permanece pendente.

## Casos planejados — registro histórico

| Caso | Entrada isolada | Resultado esperado | Estado |
| --- | --- | --- | --- |
| positivo Flask/SQLite | pedido de auditoria/refatoração MVC | seleciona a skill, executa fases 1/2 e pausa | passou com GPT-5.6; ver execução acima |
| positivo Express | LMS legado com checkout | adapta análise sem editar a skill | pendente |
| negativo | alteração textual sem arquitetura | não seleciona a skill | pendente |
| ambíguo | “melhore a organização” | esclarece objetivo antes de mutação | pendente |
| stack desconhecida | entry point/stack inconclusivos | relata limite e pede evidência | pendente |
| recusa | usuário nega após Fase 2 | nenhuma escrita | pendente |
| retomada | aprovação posterior sobre mesma revisão | salva auditoria e aplica só escopo aprovado | pendente |
| aprovação parcial | finding selecionado depende de outro | pede ampliação; não altera ambos | pendente |
| três ciclos | mesma falha sem nova hipótese | encerra incompleto | pendente |

Cada execução registrará revisão do projeto, hash do pacote, contexto efetivo,
entrada, saída, critério e resultado observado. O gabarito manual, OpenSpec,
relatórios anteriores e `docs/refactor-arch` ficarão fora da cópia avaliada.

## Baseline sem a skill

Em sessão independente e somente leitura, um agente identificou riscos relevantes e
pausou, mas propôs alterar a semântica funcional de `/admin/query` para allowlist ou
bloqueio sem uma etapa formal de diferenças/aprovação. Também propôs services como
camada geral. Essas lacunas motivaram contratos explícitos de aprovação e MVC
adaptável; a prudência existente não foi duplicada com regras desnecessárias.


## Avaliação final consolidada — 22/10/2026

O pacote final não sofreu alteração semântica durante as três transformações.
[Manifesto SHA-256 das três cópias](evidence/final-skill-manifest.json):
`1848a52ef70992701552e275e4b3d998d83e94810a3c2e6cae05317e41d3bb57`.
O hash identifica os sete arquivos completos (caminho relativo + NUL + hash por
arquivo + LF, ordenação sem distinção de caixa), não somente SKILL.md.

A [nova execução independente nos três originais](evidence/final-original-audits.md)
recebeu cópias obtidas por git archive da revisão-base com somente projeto/skill;
fontes contadas 4/3/15, contratos 19/3/22. O contexto de leitura excluiu README
raiz, OpenSpec, gabarito e relatórios prévios. Os 51 arquivos, inclusive os pacotes,
permaneceram idênticos por caminho/tamanho/hash antes/depois. A resposta de teste
“Não autorizo alterações.” encerrou as três execuções sem Fase 3. O agente não
conhecia a revisão Git na cópia sem .git; a origem foi registrada pelo preparador,
e os manifests identificam o conteúdo efetivamente analisado.

| Projeto original | CRITICAL/HIGH/MEDIUM/LOW observados na repetição | Critério |
|---|---|---|
| e-commerce Flask | 3/4/3/2 | stack correta, 12 findings, HTTP19 |
| LMS Express | 0/6/1/2 | stack correta, 9 findings, HTTP3 |
| Task Manager Flask | 1/2/4/2 | organização parcial reconhecida, 9 findings, HTTP22 |

Esses totais são de uma nova amostra e não substituem as auditorias históricas.
A amostra classificou God Class/segredos/hash com severidades diferentes da
rubrica do enunciado em alguns casos; isso é variância observada, não consenso
artificial. Todas encontraram pelo menos cinco achados e um CRITICAL/HIGH. As
classificações dos relatórios entregues foram conferidas pela rubrica. No projeto
1, C01/C08/C09/C11/C12 correspondem aos cinco IDs manuais P1-01..05. No LMS,
validação incompleta aparece dentro do finding de fronteiras/MVC, sem inventar
uma duplicação inexistente para igualar o gabarito.

| Caso | Execução e resultado observado |
|---|---|
| Positivo Flask/Express/ORM parcial | Três originais auditados em contexto novo; stacks, domínios e inventários reconhecidos |
| Negativo de acionamento | Pedido somente de correção de typo com metadata da skill: não invocou refactor-arch; mudou apenas README descartável |
| SQL parametrizado/configuração externa/rota fina | Nenhum finding correspondente; ambos controles receberam 0/0/0/0 |
| Variação estrutural | Entry e módulos renomeados, boot HTTP equivalente antes da análise; fronteiras reconhecidas |
| Ambíguo | Apresentou auditoria/diferenças e parou sem assumir aprovação |
| Stack desconhecida | Identificou falta de evidências e parou sem scaffold Flask/Express |
| Recusa | Hashes de fontes, skill e banco de fixture inalterados |
| Retomada | Auditoria salva enquanto fonte ainda tinha hash original; só depois correção autorizada; seis casos HTTP equivalentes |
| Aprovação parcial/dependência recusada | Não inventou fonte de role nem negou toda função; manteve conjunto pendente |
| Limite de ciclos | Baseline + três correções/validações realmente executadas, todos falharam; encerrou incompleto sem quarta tentativa |

[Entradas, saídas, hashes, preparação e limitações dos casos](evidence/skill-behavior-evaluation.md).
Os scripts vinculados nesse registro permitem repetir fixtures e verificações de
boot/hash. A avaliação usa novas conversas do mesmo modelo, uma amostra por caso,
sem comparação causal com agente sem skill; a simulação de ciclos não representa
três falhas reais das aplicações. Parte da avaliação de pressão compartilha
contexto. Não se alega isolamento de sistema operacional ou validade estatística.

As três auditorias iniciais foram salvas antes das mudanças. O projeto 1 teve
aprovação específica registrada; os projetos 2/3 seguem a instrução explícita
“ignore as aprovações por enquanto. continue até o fim.” Essa autorização de
sessão não removeu o gate do pacote e não foi injetada nos cenários de recusa.
As evidências reais de Fase 3 estão em
[validação1](validation-project-1.md), [validação2](validation-project-2.md) e
[validação3](validation-project-3.md), com testes, processos e matrizes completas.
A versão final já é a versão usada nessas transformações; não houve alteração de
instruções que exigisse repetir a transformação somente para sincronizar hashes.


O frontmatter das três cópias também passou em parser YAML formal (PyYAML
6.0.3 em diretório temporário, sem dependência nova das aplicações):
[log YAML](evidence/final-skill-yaml.log). Isso encerra a limitação histórica de
PyYAML ausente no Python global; a skill continua exigindo apenas arquivos Markdown.


## Segunda auditoria e revisão final

A [segunda execução sobre as três fontes refatoradas](evidence/final-refactored-reaudit.md)
reconheceu MVC existente e não fabricou God Classes nem impôs cinco findings.
Identificou regressões menores de contrato, que foram corrigidas com testes:
contagens vazias no P1 e semântica LIKE/defaults/UTF8 no P3. As correções por outro
implementador durante a auditoria aparecem explicitamente nos manifests; não
houve escrita do avaliador nas fontes. [Registro da revisão e decisões](evidence/integration-review.md).
Aprovação parcial/dependências também foi executada no caso controlado vinculado
acima. Auditoria estática não substitui a reprodução funcional em checkout limpo.

## Conferência de entrega — 23/10/2026

O relatório entregue do Task Manager foi alinhado à rubrica: P3-08 passa de HIGH
para CRITICAL, com total 2/2/3/2 (nove achados). A amostra independente e seus
totais originais acima são preservados como resultados observados, sem edição
retroativa. README, auditoria e validação usam a classificação revisada.

A evidência do gate é distinta da autorização das transformações: nas três
reanálises dos originais, a recusa encerrou as execuções sem escrita; uma fixture
separada comprova retomada e persistência antes da correção. As transformações
iniciais dos projetos 2/3 usaram dispensa expressa de pausas, não confirmação
específica após cada relatório. O README explicita essa diferença. Não se afirma
que a revisão de hoje criou aprovação retroativa ou repetiu as transformações.
