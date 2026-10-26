# Refactor Architecture — desafio de Custom Skills

Skill **refactor-arch**, executada com OpenAI Codex nas três APIs do desafio.
Os 32 arquivos originais foram conferidos antes da execução. A cronologia,
aprovação e responsabilidades estão no
[registro da execução](reports/skill-execution.md).

## Análise Manual

O levantamento preparatório que orientou a construção da skill está consolidado
abaixo, referindo-se ao **código original**. As auditorias ampliam esse
levantamento conforme os critérios de aceite. Cada projeto inclui um
CRITICAL/HIGH, dois
MEDIUM e dois LOW; esta seleção não representa todos os achados.

| Projeto | Severidade | Evidência original | Problema e relevância | Auditoria nova |
| --- | --- | --- | --- | --- |
| Loja Flask | CRITICAL | models.py:109–110,126–128 | SQL concatenado permite alterar consultas/login e quebra apóstrofos legítimos. | F01 |
| Loja Flask | MEDIUM | models.py:170–202,235–273 | Consultas por pedido/item crescem com o volume: N+1. | F10 |
| Loja Flask | MEDIUM | controllers.py:5–126 | Validação/serialização duplicadas divergem entre operações. | F11 |
| Loja Flask | LOW | models.py:256–262; controllers.py:52,242 | Limiares de desconto/status sem nomes dificultam manter regras. | F15 |
| Loja Flask | LOW | models.py:2; database.py:2 | Imports sqlite3/os sem uso tornam imprecisas as dependências aparentes. | F16 |
| LMS Express | CRITICAL | src/AppManager.js:4–144 | Uma classe concentra schema, HTTP, checkout, pagamento e relatório sem isolamento. | E02 |
| LMS Express | MEDIUM | src/AppManager.js:89–127 | Consultas financeiras dentro de loops provocam N+1. | E08 |
| LMS Express | MEDIUM | src/AppManager.js:29–35,46,132–133 | Truthiness não valida tipos; card numérico pode quebrar callback. | E10 |
| LMS Express | LOW | src/AppManager.js:46,63,81 | Prefixo de aprovação/estados dispersos escondem regras de domínio. | E11 |
| LMS Express | LOW | src/AppManager.js:28–35,89–127 | Nomes internos abreviados dificultam rastrear dados; chaves HTTP devem ser preservadas. | E12 |
| Task Manager | CRITICAL | models/user.py:16–25; routes/user_routes.py:33–40 | Respostas expõem hash de senha e facilitam quebra offline. | T01 |
| Task Manager | MEDIUM | routes/task_routes.py:14–57; routes/report_routes.py:53–68 | Consultas por entidade e agregações em memória causam gargalos. | T09 |
| Task Manager | MEDIUM | models/task.py:23–36,50–60; routes/task_routes.py:17–39 | Regras de atraso/serialização duplicadas podem divergir entre respostas. | T10 |
| Task Manager | LOW | routes/task_routes.py:96–114; routes/user_routes.py:64–72 | Limites e estados repetidos dificultam manutenção coerente. | T12 |
| Task Manager | LOW | app.py:7; routes/report_routes.py:24–28 | Imports sem uso e variáveis p1..p5 escondem dependências/significado. | T13 |

Linhas completas, impactos e propostas constam das auditorias e continuam
referindo-se ao original mesmo quando os arquivos foram movidos.

## Construção da Skill

Entrada canônica: [SKILL.md](code-smells-project/.agents/skills/refactor-arch/SKILL.md).
O pacote contém nove arquivos e é copiado integralmente para os três projetos.

| Referência | Responsabilidade |
| --- | --- |
| project-analysis.md | Stack, versões, domínio, fontes, arquitetura e inventário HTTP. |
| anti-patterns.md | Doze famílias AP-01–AP-12, severidades, evidência e falsos positivos. |
| audit-report-template.md | Achados, linhas originais, dependências, contratos e aprovação. |
| mvc-guidelines.md | Models, Views/Routes, Controllers e serviços quando necessários. |
| refactoring-playbook.md | Doze transformações antes/depois: 24 blocos de código. |
| validation.md | Caracterização, regressão, boot real, endpoints e reauditoria. |
| regression-checks.md | Defaults/tipos, identidade atual, concorrência, migração e ambientes. |
| delivery.md | Relatórios, documentação, autoria e reprodução limpa da entrega. |

O catálogo cobre SQL injection, segredos/dados sensíveis, God Class, senhas/tokens,
autorização, estado global, transações parciais, N+1, duplicação, APIs deprecated,
magic values e nomes/código morto. A escolha decorre dos originais. A severidade
exige evidência: separação parcial não implica God Class; ORM não implica SQL
injection; deprecation exige versão aplicável e referência oficial.

Fases 1/2 são somente leitura, sem instalação, boot, banco ou relatório escrito.
A Fase 2 apresenta achados e diferenças de contrato e **para**. A Fase 3 salva a
auditoria após aprovação, caracteriza contratos e produz código, testes, correções
e documentação em incrementos. A aprovação desta execução foi:
**“Aprovo o escopo completo apresentado”**.

As regras usam responsabilidades e evidências, sem impor stack. A loja precisa de
conexão por contexto e SQL parametrizado; o Express exige separar a God Class e
serializar transações assíncronas; o Task Manager conserva Models úteis e extrai
Controllers das Routes. Mudanças de segurança/migração são diferenças explícitas,
sem eliminar funcionalidades nem impor políticas comerciais de outra solução.

A revisão reforçou a responsabilidade da própria skill pelo ciclo inteiro. Os
executores começaram em contextos separados e isolados. Uma avaliação
comportamental conferiu as instruções; ela não substitui os testes das aplicações.

## Resultados

| Projeto | Stack / fontes originais | CRITICAL | HIGH | MEDIUM | LOW | Total | Contratos |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Loja](reports/audit-project-1.md) | Python/Flask, 4 | 3 | 6 | 5 | 2 | 16 | 19 |
| [LMS](reports/audit-project-2.md) | Node.js/Express, 3 | 2 | 5 | 3 | 3 | 13 | 3 |
| [Task Manager](reports/audit-project-3.md) | Python/Flask, 15 | 2 | 5 | 4 | 2 | 13 | 22 |

Cada auditoria encontrou os cinco problemas da seleção manual correspondente.
As contagens iniciais não incluem suspeitas de deprecation ainda não verificadas.
Atualizações com runtime/documentação ficam na validação, sem inventar evidência
para a fase somente leitura.

As três Fases 3 foram concluídas pela skill e revisadas. Resultado funcional atual:

| Projeto | Suíte | HTTP real | Revisão independente |
| --- | ---: | ---: | --- |
| Loja | 66/66 | 19 contratos, 40 casos | Duplicatas, corrida da listagem e inteiros SQLite corrigidos em RED/GREEN |
| LMS | 21/21 | 3 contratos, 42 casos | IDs órfãos de usuário/matrícula corrigidos; revisor repetiu suíte e HTTP |
| Task Manager | 28/28 | 22 contratos + 34 checks de segurança | Status NULL e token após reutilização de ID corrigidos em RED/GREEN |

Comparação estrutural: a loja passou de quatro arquivos cruzando HTTP/SQL/regras
para factory + `routes/controllers/models/services`; o LMS substituiu a God Class
por composição + `routes/controllers/models/services/database/security`; o Task
Manager preservou seus Models e extraiu Controllers, store, security, validação e
factory das Routes. Os detalhes estão nos READMEs dos projetos e em
[validação 1](reports/validation-project-1.md),
[validação 2](reports/validation-project-2.md) e
[validação 3](reports/validation-project-3.md).

Checklist aplicado aos três projetos:

- [x] linguagem, framework, domínio e fontes detectados na Fase 1;
- [x] relatório no template, linhas originais, severidades ordenadas e pelo menos cinco achados;
- [x] aprovação humana real antes da primeira edição;
- [x] Models, Views/Routes e Controllers explícitos, config e erros centralizados;
- [x] aplicação inicia em processo real com dados descartáveis;
- [x] todos os métodos/caminhos originais respondem, incluindo sucesso autorizado e recusas;
- [x] regressões encontradas por revisão receberam teste RED, correção e GREEN;
- [x] as três cópias completas da skill têm hashes iguais.

Os logs versionados são medições desta execução e tiveram caminhos locais
substituídos por marcadores. O LMS mantém como risco residual os 14 advisories do
lock original (2 critical, 8 high, 1 moderate, 3 low), documentados sem alegar
correção fora de E01–E13. A reprodução final em checkout limpo é registrada no
relatório de integração.

## Como Executar

Requer Git, OpenAI Codex instalado/autenticado, Python 3.12 e Node.js 24 com npm.
A documentação oficial confirma a descoberta em .agents/skills a partir do
diretório de execução e a invocação por $ ou /skills:
[Build skills](https://learn.chatgpt.com/docs/build-skills), consultada em 23/10/2026.

Abra Codex dentro de cada projeto para descobrir a skill local:

```powershell
cd code-smells-project
codex
# No prompt do Codex: $refactor-arch

cd ../ecommerce-api-legacy
codex
# No prompt do Codex: $refactor-arch

cd ../task-manager-api
codex
# No prompt do Codex: $refactor-arch
```

Revise a auditoria e aprove explicitamente a Fase 3. Uma nova execução no código
corrigido não deve reproduzir achados do original. Para avaliar detecção nos
legados, use uma cópia limpa dos projetos originais com a skill instalada.

Na raiz, em checkout limpo, instale e valide com uma pasta de saída nova:

```powershell
python scripts/reproduce.py --output ../refactor-validation
```

Esse runner instala ambientes e executa regressões e boot/HTTP real, salva logs e
summary.json e falha se qualquer etapa falhar. As matrizes HTTP possuem seus
próprios processos, portas e bancos descartáveis. O verificador isolado
`python scripts/check_delivery.py` confere estrutura, referências e cópias; não
prova funcionamento, qualidade dos achados ou aprovação humana.

Inicialização, configuração, provisão, migração e rollback específicos estão nos
READMEs de cada projeto.
