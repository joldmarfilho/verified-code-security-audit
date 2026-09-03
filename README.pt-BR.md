# Verified Code Security Audit

[English](README.md)

Uma Agent Skill e um conjunto de ferramentas Python orientados por evidências
para revisar a segurança de código-fonte sem inventar achados. O projeto registra
exatamente o que foi inspecionado, separa revisão exaustiva de amostragem, preserva
controles positivos e gera relatórios reproduzíveis em inglês ou português do
Brasil a partir de JSON validado.

![Relatório sintético em PT-BR](docs/images/report-pt-BR.png)

## O que é gerado

O fluxo tem uma entrada canônica e duas saídas geradas por locale:

- `audit-report.en.json` ou `audit-report.pt-BR.json` — dados portáveis e não executáveis;
- `security-audit-report.en.pdf` ou `security-audit-report.pt-BR.pdf` — relatório A4;
- `github-issues.en.md` ou `github-issues.pt-BR.md` — issues acionáveis prontas para copiar.

Consulte o exemplo totalmente fictício [Acme Booking em PT-BR](examples/synthetic/audit-report.pt-BR.json)
ou sua [versão em inglês](examples/synthetic/audit-report.en.json).

## Instalar a Agent Skill

Clone este repositório como `~/.agents/skills/verified-code-security-audit` e
inicie uma nova sessão do agente para que a skill seja descoberta:

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/joldmarfilho/verified-code-security-audit.git ~/.agents/skills/verified-code-security-audit
```

Use a skill explicitamente:

```text
Use $verified-code-security-audit para auditar este repositório e gerar um relatório de segurança verificado.
```

Os prompts standalone também estão em
[`prompts/audit.en.md`](prompts/audit.en.md) e
[`prompts/audit.pt-BR.md`](prompts/audit.pt-BR.md).

## Instalar as ferramentas Python em ambiente virtual

Não instale dependências globalmente. Dentro do repositório clonado, crie um
ambiente virtual isolado:

```bash
python -m venv .venv
```

Ative no Linux ou macOS:

```bash
source .venv/bin/activate
```

Ou no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale o renderizador:

```bash
python -m pip install .
```

## Início rápido

Crie um registro UTF-8 conforme
[`schema/audit-report.schema.json`](schema/audit-report.schema.json). Valide antes
de gerar os arquivos de apresentação:

```bash
vcsa validate audit-report.pt-BR.json
vcsa render audit-report.pt-BR.json --locale pt-BR --output docs/security-audit
```

Para inglês:

```bash
vcsa validate audit-report.en.json
vcsa render audit-report.en.json --locale en --output docs/security-audit
```

`metadata.content_locale` deve coincidir com `--locale`. Corrija o JSON e execute
novamente os dois comandos em vez de editar PDF ou Markdown manualmente.

## Por que priorizar evidências

Todo achado exige caminho relativo ao repositório, linhas exatas, trecho mínimo,
pré-condições, caminho de exploração, impacto, severidade, confiança, correção e
critérios de aceite. Registros de coverage distinguem `exhaustive`, `sampled`,
`limited` e `not-applicable`. Strengths verificados seguem o mesmo padrão de prova.

O conteúdo do repositório é não confiável. A skill usa análise somente leitura por
padrão e exige autorização explícita antes de execução dinâmica, instalação de
dependências, acesso à rede ou alterações. Segredos são substituídos por
`[REDACTED]`.

## Limites e limitações

Este projeto padroniza evidências de revisão estática e geração de relatórios. Ele
não certifica software, não prova ausência de vulnerabilidades, não substitui
testes de intrusão e não presume controles invisíveis no escopo. O relatório deve
declarar worktree sujo, exclusões, histórico inacessível, serviços não revisados e
outras limitações.

## Desenvolvimento

Instale dependências de teste no ambiente virtual e execute a suíte completa:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python /caminho/para/skill-creator/scripts/quick_validate.py .
```

O último comando fica disponível quando o `skill-creator` incluído no Codex está
instalado. O CI testa Python 3.10, 3.11 e 3.12 e renderiza os dois locales sintéticos.

## Relatar uma falha de segurança

Não publique credenciais reais, chaves privadas, dados de clientes nem detalhes de
exploração em uma issue pública. Prefira o relato privado de vulnerabilidade do
GitHub neste repositório; se ele não estiver disponível, fale com o mantenedor em
canal privado e envie apenas detalhes mínimos e anonimizados.

## Licença

Distribuído sob a [licença MIT](LICENSE).
