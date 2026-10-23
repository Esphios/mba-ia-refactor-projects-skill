# Matriz de rastreabilidade

## Critérios obrigatórios

| Requisito | Artefato planejado | Tarefas | Evidência de aceite |
| --- | --- | --- | --- |
| Análise manual: 5 achados/projeto e distribuição de severidade | README, revisão-base | 1.1–1.2 | IDs P1/P2/P3, arquivo, linhas e justificativa |
| Skill `refactor-arch` portátil e invocável | três `.agents/skills/refactor-arch` | 2.1–2.8, 4.1, 5.1 | YAML, links, hashes e invocações registradas |
| Três fases e confirmação antes de escrita | SKILL.md e auditorias | 2.1, 3.1–3.2, 4.2, 5.2 | conversa/registro de pausa, aprovação e revisão |
| Cinco áreas de referência, 8+ padrões e transformações | `references/*.md` | 2.2–2.5 | validação estrutural e revisão de conteúdo |
| Auditoria rastreável real nos três projetos | `reports/audit-project-{1,2,3}.md` | 3.1–3.2, 4.2, 5.2 | 5+ findings/projeto, linhas, revisão e severidades |
| MVC explícito preservando funcionalidades | código dos três projetos | 3.4–3.6, 4.4–4.5, 5.4–5.6 | fronteiras revisadas e testes de fluxo |
| Todos os contratos HTTP e boot real | inventário e validations | 1.3, 1.6, 3.3/3.7, 4.3/4.6, 5.3/5.7 | matrizes 19/3/22 e logs sanitizados |
| Segurança, autorização, integridade e legado | código, testes e decisões aprovadas | 1.6, 3.5–3.6, 4.5, 5.5 | positivos/negativos, rollback e banco legado |
| README com construção, resultados e execução | README | 6.3–6.4 | comandos reproduzíveis, árvores e checklists |
| Fork público versionado sem segredos/bancos | histórico e remoto autorizado | 7.1–7.3 | `git ls-files`, URL/visibilidade e checkout limpo |

## Avaliações adicionais

| Avaliação | Artefato planejado | Tarefas | Evidência |
| --- | --- | --- | --- |
| Trigger positivo, negativo e ambíguo; recusa/retomada | `reports/skill-evaluation.md` | 2.6, 6.1 | entrada, versão, saída e resultado observado |
| Stack desconhecida e projeto parcialmente organizado | mesmo relatório | 2.2, 2.6 | limitação honesta e detecção contextual |
| Controles negativos e variação estrutural | cópias descartáveis + relatório | 6.5 | falso positivo/omissão por caso e boot equivalente |
| Segunda auditoria e aprovação parcial | relatório de avaliação | 2.7, 6.6 | ausência de findings forçados/ampliação implícita |
| Congelamento e estabilidade da versão final | hashes e reauditorias | 6.2 | três cópias iguais e versões identificadas |
| Validador auxiliar da entrega | `scripts/validate-delivery.py` | 6.7 | passa completo e falha em cópia incompleta |

Avaliações adicionais não substituem qualquer linha da seção obrigatória.

## Conferência da análise manual — 22/10/2026

Revisão-base: `6d1ce6248c3e956801010a89d8bdaab48029bf30`. Esta correção é
posterior ao pacote inicial, sem alterar a cronologia da análise inicial.
Cada intervalo foi conferido no conteúdo original via `git show`.

| IDs | Evidências relativas ao projeto | Distribuição conferida |
| --- | --- | --- |
| P1-01 a P1-05 | models.py:105-112; models.py:171-232; controllers.py:24-96; models.py:256-262; models.py:2 | 1 CRITICAL, 2 MEDIUM, 2 LOW |
| P2-01 a P2-05 | src/AppManager.js:4-140; :80-127; :29-35; :29-33; src/utils.js:10,25 e src/AppManager.js:2 | 1 CRITICAL, 2 MEDIUM, 2 LOW |
| P3-01 a P3-06 | models/user.py:16-25; routes/task_routes.py:14-58; :16-37,70-80; :7; :110-113; models/user.py:27-32 | 1 CRITICAL, 1 HIGH, 2 MEDIUM, 2 LOW |

P2-05 inclui o importador sem uso. P3-01 trata da exposição do hash;
P3-06 trata separadamente do algoritmo MD5. Os IDs serão comparados com a saída
independente da skill depois da avaliação; esta matriz não comprova invocação.
