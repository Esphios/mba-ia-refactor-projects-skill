# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Análise Manual

A análise manual inicial usou a revisão
`6d1ce6248c3e956801010a89d8bdaab48029bf30`. A conferência de 22/10/2026,
posterior ao pacote inicial da skill, corrigiu evidências e separou exposição de
hash de armazenamento MD5. As linhas permanecem resolvíveis na revisão-base e
formam o gabarito de comparação para a auditoria independente.

### Projeto 1 — code-smells-project

| ID | Severidade | Evidência | Justificativa |
| --- | --- | --- | --- |
| P1-01 | CRITICAL | `models.py:105-112` | O login concatena email e senha no SQL; entrada controla a consulta e pode contornar a autenticação. |
| P1-02 | MEDIUM | `models.py:171-232` | Pedidos e itens são consultados dentro de laços, fazendo o número de queries crescer com os resultados. |
| P1-03 | MEDIUM | `controllers.py:24-96` | Criação e edição duplicam validação e já divergem nas regras de nome e categoria. |
| P1-04 | LOW | `models.py:256-262` | Limites e percentuais de desconto aparecem como literais sem nomes, ocultando a regra de negócio. |
| P1-05 | LOW | `models.py:2` | `sqlite3` é importado sem uso no módulo, adicionando uma dependência aparente e ruído. |

### Projeto 2 — ecommerce-api-legacy

| ID | Severidade | Evidência | Justificativa |
| --- | --- | --- | --- |
| P2-01 | CRITICAL | `src/AppManager.js:4-140` | Uma God Class reúne schema, seed, rotas, checkout, SQL, relatório e exclusão, ampliando acoplamento e impacto de falhas. |
| P2-02 | MEDIUM | `src/AppManager.js:80-127` | Relatório executa consultas aninhadas por curso e matrícula, produzindo N+1. |
| P2-03 | MEDIUM | `src/AppManager.js:29-35` | A entrada é validada apenas por truthiness; tipos incorretos chegam a operações de string e persistência. |
| P2-04 | LOW | `src/AppManager.js:29-33` | Variáveis internas `u`, `e`, `p`, `cid` e `cc` dificultam rastrear o checkout sem benefício de contrato. |
| P2-05 | LOW | `src/utils.js:10,25`; `src/AppManager.js:2` | `totalRevenue` é declarado/exportado em utils e importado sem uso em AppManager, adicionando dependência aparente e ruído. |

### Projeto 3 — task-manager-api

| ID | Severidade | Evidência | Justificativa |
| --- | --- | --- | --- |
| P3-01 | CRITICAL | `models/user.py:16-25` | A serialização retorna o hash de senha nas respostas, expondo dado sensível e permitindo tentativas offline. |
| P3-02 | MEDIUM | `routes/task_routes.py:14-58` | A listagem busca usuário e categoria para cada tarefa, causando N+1. |
| P3-03 | MEDIUM | `routes/task_routes.py:16-37,70-80` | Serialização e cálculo de atraso são duplicados e divergem do model. |
| P3-04 | LOW | `routes/task_routes.py:7` | Imports `json`, `os`, `sys` e `time` não usados escondem as dependências efetivas. |
| P3-05 | LOW | `routes/task_routes.py:110-113` | Limites de prioridade 1 e 5 são repetidos apesar de já existirem constantes em `utils`. |
| P3-06 | HIGH | `models/user.py:27-32` | MD5 é rápido e sem salt individual; não é mecanismo adequado para armazenar senhas. |

Além desses dezesseis itens, a auditoria deverá verificar segredos fixos,
exposição em health/logs, autorização administrativa, token falso, atomicidade e
APIs deprecated conforme a versão realmente aplicável. O inventário completo de
contratos e a matriz de autorização estão em `reports/planning/contracts.md`.

## Construção da Skill

A solução usa Codex com um pacote autossuficiente por projeto. A cópia canônica
fica em [code-smells-project/.agents/skills/refactor-arch](code-smells-project/.agents/skills/refactor-arch/SKILL.md).
As cópias de [Express](ecommerce-api-legacy/.agents/skills/refactor-arch/SKILL.md)
e [Task Manager](task-manager-api/.agents/skills/refactor-arch/SKILL.md) possuem o
mesmo conteúdo. O manifesto final e as avaliações estão em
[skill-evaluation.md](reports/skill-evaluation.md).

```text
.agents/skills/refactor-arch/
  SKILL.md
  references/
    project-analysis.md
    anti-patterns.md
    audit-report-template.md
    mvc-guidelines.md
    refactoring-playbook.md
    validation.md
```

O arquivo principal coordena análise, auditoria e transformação; referências são
lidas conforme a fase. O catálogo reúne doze famílias: SQL injection, segredos,
God Class, senhas/tokens, autorização, estado compartilhado, escritas parciais,
N+1, duplicação, deprecações, valores mágicos e nomes/código morto. Cada família
possui exemplo concreto antes/depois, explicação, contexto e verificação. As quatro
severidades seguem impacto e evidência; SQL parametrizado não é injection, e uma
API antiga não é automaticamente deprecated.

A portabilidade vem das responsabilidades MVC e da descoberta por manifests,
imports e fluxos completos. SQLite direto recebe conexão por contexto; SQLite
callback exige serializar toda a transação; ORM aproveita entidades e blueprints
existentes. Serviços adicionais coordenam transações e integrações, sem substituir
Models, Views/Routes e Controllers. O pacote não depende de caminhos absolutos,
skills pessoais ou bibliotecas de uma stack específica. Texto e exemplos são
próprios; a implementação de referência fornecida não é distribuída.

Os principais desafios foram preservar operações administrativas legítimas,
separar contratos inseguros de regressões, migrar senhas sem apagar dados e testar
integridade sob falha. O console SQL do projeto 1 continua funcional para admin;
o projeto 2 preserva histórico financeiro; o projeto 3 verifica identidade e
propriedade em cada domínio. Falsos positivos, recusa, seleção parcial e limite de
três ciclos são avaliados separadamente dos testes das aplicações.

A skill mantém aprovação humana entre fases 2 e 3. Nesta entrega o usuário
substituiu expressamente as pausas restantes por “ignore as aprovações por
enquanto. continue até o fim.” Essa exceção de sessão é registrada nas auditorias
e não altera o procedimento reutilizável nem conta como teste de aprovação.

## Resultados

Os números abaixo pertencem às auditorias iniciais dos legados, anteriores à
refatoração. Os exemplos e mínimos do enunciado acima não são resultados medidos.

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Auditoria e validação |
|---|---:|---:|---:|---:|---:|---|
| Flask e-commerce | 5 | 4 | 4 | 2 | 15 | [auditoria](reports/audit-project-1.md), [validação](reports/validation-project-1.md) |
| Express LMS | 2 | 4 | 1 | 2 | 9 | [auditoria](reports/audit-project-2.md), [validação](reports/validation-project-2.md) |
| Flask Task Manager | 1 | 3 | 3 | 2 | 9 | [auditoria](reports/audit-project-3.md), [validação](reports/validation-project-3.md) |

Comparação estrutural, excluindo dependências, bancos e caches:

```text
Projeto 1 antes                 Projeto 1 depois
app.py                         app.py + config.py + auth.py + errors.py
database.py                    database.py
models.py                      models/{product,user,order,report}_model.py
controllers.py                 controllers/ + routes/ + services/
                               tests/ + .agents/skills/refactor-arch/

Projeto 2 antes                 Projeto 2 depois
src/app.js                     src/app.js + src/server.js
src/AppManager.js              src/config/ + src/db/ + src/models/
src/utils.js                   src/controllers/ + src/routes/
                               src/services/ + src/middleware/
                               test/ + .agents/skills/refactor-arch/

Projeto 3 antes                 Projeto 3 depois
app.py + database.py           app factory + config + auth + errors
models/                        models/ + controllers/
routes/ com regras/queries     routes/ finas, categorias separadas
services/ + utils/             services/ + utils/ compartilhados
seed.py                        seed explícito + tests/ + .agents/skills/
```

As verificações individuais, contagens de testes, resultados HTTP e mapeamento
de cada finding estão nos três relatórios de validação. A matriz cobre **19, 3 e
22 pares originais método/caminho**, com sucesso autorizado nos endpoints
protegidos. O login adicional do LMS é validado separadamente. Logs de falhas do
baseline e testes RED permanecem como evidência histórica, identificados pelo
nome; não representam falha do estado final.

Checklist individual da solução (o checklist anterior é o modelo do enunciado):

| Critério | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Linguagem/framework/domínio detectados | [x] Python/Flask/e-commerce | [x] JS/Express/LMS | [x] Python/Flask/tarefas |
| Contagem real de fontes originais | [x] 4 | [x] 3 | [x] 15 |
| Relatório com revisão, evidências e linhas | [x] auditoria1 | [x] auditoria2 | [x] auditoria3 |
| Findings ordenados e mínimo de cinco | [x] 15 | [x] 9 | [x] 9 |
| Pelo menos um CRITICAL/HIGH | [x] | [x] | [x] |
| Deprecações avaliadas por versão | [x] sem caso confirmado | [x] sem API confirmada | [x] Query.get/utcnow |
| Gate de confirmação da skill | [x] aprovação específica | [x] waiver + recusa avaliada | [x] waiver + recusa avaliada |
| Diretórios e responsabilidades MVC | [x] | [x] | [x] |
| Configuração externa | [x] | [x] | [x] |
| Models abstraem persistência | [x] | [x] | [x] |
| Views/Routes separadas | [x] | [x] | [x] |
| Controllers coordenam fluxos | [x] | [x] | [x] |
| Erros centralizados | [x] | [x] | [x] |
| Entry point e boot real | [x] app.py | [x] server.js | [x] app.py/factory |
| Contratos originais com sucesso autorizado | [x] 19/19 | [x] 3/3 | [x] 22/22 |
| Senhas/identidade/admin/propriedade testados | [x] | [x] | [x] |
| Integridade, rollback e legado testados | [x] | [x] | [x] |

As células apontam para as auditorias/validações vinculadas na tabela de resultados;
nenhuma negação de acesso conta como substituto de um sucesso autorizado.

O [relatório da skill](reports/skill-evaluation.md) separa descoberta/invocação,
auditorias independentes dos originais, controles negativos, variação estrutural,
recusa/retomada, aprovação parcial e segunda auditoria. Testes HTTP e boot são
evidência de execução; o [validador estrutural](scripts/validate-delivery.py)
confere arquivos, exemplos, links e igualdade dos pacotes, sem substituir esses
testes nem revisão humana.

## Como Executar

Pré-requisitos: Git, Python 3.12, Node.js 24 com npm, acesso ao registro de
dependências e Codex instalado/autenticado. Os runtimes efetivamente usados ficam
registrados nos relatórios. SQLite é local; pagamento é simulado e SMTP fica
desabilitado, sem cobrança ou envio externo.

Para invocar a skill, entre em um projeto e inicie Codex:

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

Informe o destino `../reports/audit-project-N.md` quando quiser um novo relatório.
Preserve as auditorias históricas usando outro nome em reexecuções. Revise o
relatório e diferenças de contrato antes de autorizar transformação. A instalação
local em `.agents/skills` e invocação explícita seguem a
[documentação oficial do Codex](https://learn.chatgpt.com/docs/build-skills).

Para reproduzir a entrega inteira a partir da raiz:

```powershell
python scripts/reproduce-delivery.py
python scripts/validate-delivery.py
python -m unittest discover -s scripts/tests -v
```

O primeiro comando cria ambientes Python locais quando necessário, instala
requirements-dev e o lockfile npm, executa as três suítes e inicia processos reais
com configurações temporárias. Usa bancos descartáveis e encerra os servidores.
O log fica em `reports/evidence/reproduction.log`. Para repetir sem reinstalar:
`python scripts/reproduce-delivery.py --skip-install`. Também aceita
`--root <checkout>` e `--output <log>` para reprodução em checkout limpo.

Setup interativo, configuração, seed opcional e testes isolados estão nos READMEs
de [e-commerce Flask](code-smells-project/README.md),
[LMS Express](ecommerce-api-legacy/README.md) e
[Task Manager](task-manager-api/README.md). Cada exemplo de ambiente contém somente
placeholders; defina valores novos localmente. Os projetos Flask usam porta 5000
por padrão: execute um por vez ou configure portas diferentes.

Antes de usar banco existente, faça backup verificado e teste em uma cópia. Não
execute o seed destrutivo legado do Task Manager sobre dados existentes. Os boots
refatorados não apagam bancos; seeds são explícitos. Senhas legadas são atualizadas
somente após login válido, conforme o prazo documentado por projeto. No LMS,
usuários vinculados são desativados mantendo matrícula/pagamento, e usuários sem
vínculos podem ser removidos fisicamente. Rollback exige o código e backup de banco
correspondentes: hashes fortes não devem ser revertidos para os formatos inseguros.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.
