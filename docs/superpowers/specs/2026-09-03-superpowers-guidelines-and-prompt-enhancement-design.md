# Especificação de Design: Integração com Superpowers e Melhoria dos Prompts

**Data:** 2026-09-03  
**Status:** Aprovado  
**Referência Externa:** [Superpowers](https://github.com/obra/superpowers)

---

## 1. Visão Geral e Objetivos

O projeto **Verified Code Security Audit** estabelece um padrão rigoroso de auditoria de código-fonte baseado em evidências, eliminando falsos positivos e "alucinações" de segurança por meio de um contrato de dados canônico (`JSON Schema`) e renderização determinística (`vcsa`).

Para maximizar a eficácia dos agentes de inteligência artificial (Codex, Claude Code, Antigravity, etc.) que executam essa auditoria, este design incorpora as diretrizes de disciplina operacional da skill [`using-superpowers`](https://github.com/obra/superpowers).

Objetivos principais:
1. **Prompts (`prompts/audit.pt-BR.md` e `prompts/audit.en.md`):** Incluir disciplina operacional com checklist de tarefas obrigatório, tabela de anti-racionalização (*Red Flags* específicas de auditoria) e portão de verificação pré-conclusão (*verification-before-completion*).
2. **Habilidade do Agente (`SKILL.md`):** Adicionar diretrizes de orquestração com o ecossistema Superpowers (gerenciamento ativo de tarefas, rastreamento sistemático de vulnerabilidades e comprovação estrita).
3. **Documentação (`README.md` e `README.pt-BR.md`):** Mencionar a compatibilidade e alinhamento do projeto com o ecossistema Superpowers, destacando o link oficial (`https://github.com/obra/superpowers`).

---

## 2. Detalhamento das Alterações

### 2.1 Prompts de Auditoria (`prompts/audit.pt-BR.md` e `prompts/audit.en.md`)

Os prompts receberão uma nova seção logo após a definição do escopo inicial:
- **Disciplina Operacional & Rastreamento de Tarefas:** Exigência de que o agente mantenha um checklist/artefato de tarefas para as Fases 1 a 5, atualizando o status (`- [x]`) antes de avançar.
- **Tabela de Anti-Racionalização (Pensamentos Proibidos vs. Realidade):**
  - *Pensamento:* "O repositório é pequeno, posso pular o snapshot/inventário." $\rightarrow$ *Realidade:* Toda auditoria requer escopo, snapshot e inventário explícitos de superfícies antes de inspecionar código.
  - *Pensamento:* "Posso amostrar 3 arquivos e marcar a cobertura como completa." $\rightarrow$ *Realidade:* Amostragem nunca é exaustiva. Registre honestamente contagens descobertas/revisadas e declare `sampled` ou `limited`.
  - *Pensamento:* "O JSON parece visualmente correto, não preciso rodar `vcsa validate`." $\rightarrow$ *Realidade:* `vcsa validate` é obrigatório. Erros de schema invalidam todo o entregável.
  - *Pensamento:* "Posso afirmar que a aplicação está totalmente segura." $\rightarrow$ *Realidade:* Proibido. Declare apenas a ausência de achados no escopo inspecionado sob as limitações declaradas.
- **Portão de Verificação Pré-Conclusão (*Verification-Before-Completion*):** Obrigatoriedade de comprovar visualmente e estruturalmente a geração do PDF e do Markdown de issues antes de emitir a resposta final.
- **Referência:** Menção de conformidade com as diretrizes do [Superpowers](https://github.com/obra/superpowers).

### 2.2 Arquivo de Habilidade (`SKILL.md`)

- Adição de nota de orquestração para agentes com o plugin [Superpowers](https://github.com/obra/superpowers):
  - Invocação e execução com `using-superpowers`.
  - Uso de investigação com disciplina de `systematic-debugging` para provar caminhos de exploração.
  - Validação estrita via `verification-before-completion` antes de marcar a auditoria como pronta.

### 2.3 Documentação (`README.md` e `README.pt-BR.md`)

- Inclusão de menção ao [Superpowers](https://github.com/obra/superpowers) na seção de ecossistema de habilidades e agentes.
- Explicação clara de como o Superpowers potencializa a execução sem atalhos ou desvios de processo.

---

## 3. Critérios de Validação

1. **Testes Unitários:** Executar `python -m unittest discover -s tests` para garantir que nenhuma alteração textual quebrou fixtures ou testes existentes.
2. **Integridade de Documentação:** Verificar que todos os links para `https://github.com/obra/superpowers` estão válidos e formatados corretamente.
3. **Bilinguismo:** Garantir paridade e coerência conceitual idêntica entre as versões em inglês e português.
