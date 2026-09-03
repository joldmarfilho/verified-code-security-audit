# Superpowers Guidelines and Prompt Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Incorporate operational discipline guidelines from [Superpowers](https://github.com/obra/superpowers) into the audit prompts (`prompts/audit.*.md`), update `SKILL.md` to reference Superpowers practices, and document Superpowers integration in `README.md` and `README.pt-BR.md`.

**Architecture:** Update prompt instructions and agent skill definitions to enforce task tracking, an anti-rationalization table (red flags), and a verification-before-completion gate. Update bilingual documentation with proper badges and ecosystem integration notes.

**Tech Stack:** Markdown, Python unittest, Git, JSON Schema.

## Global Constraints

- Never use patch scripts, ps1, or py scripts for file modifications; always perform surgical diff edits.
- All responses must be in Brazilian Portuguese.
- Preserve bilingual parity between EN and PT-BR files.
- All existing tests in `tests/` must continue to pass.
- Superpowers repository URL: `https://github.com/obra/superpowers`.

---

### Task 1: Update Portuguese Prompt (`prompts/audit.pt-BR.md`)

**Files:**
- Modify: `prompts/audit.pt-BR.md`

**Interfaces:**
- Consumes: Existing 5 phases in `prompts/audit.pt-BR.md`.
- Produces: Enhanced prompt with Operational Discipline, Anti-Rationalization Red Flags, Task Tracking, and Verification-Before-Completion referencing Superpowers.

- [ ] **Step 1: Inspect target location in `prompts/audit.pt-BR.md`**
- [ ] **Step 2: Apply surgical diff using `replace_file_content` to add the Operational Discipline section**
- [ ] **Step 3: Verify markdown formatting and links**
- [ ] **Step 4: Commit changes**

```bash
git add prompts/audit.pt-BR.md
git commit -m "docs(prompts): add operational discipline and superpowers guidelines to pt-BR prompt"
```

---

### Task 2: Update English Prompt (`prompts/audit.en.md`)

**Files:**
- Modify: `prompts/audit.en.md`

**Interfaces:**
- Consumes: Existing 5 phases in `prompts/audit.en.md`.
- Produces: Symmetric English prompt with Operational Discipline, Anti-Rationalization Red Flags, Task Tracking, and Verification-Before-Completion referencing Superpowers.

- [ ] **Step 1: Inspect target location in `prompts/audit.en.md`**
- [ ] **Step 2: Apply surgical diff using `replace_file_content` to add the Operational Discipline section**
- [ ] **Step 3: Verify markdown formatting and links**
- [ ] **Step 4: Commit changes**

```bash
git add prompts/audit.en.md
git commit -m "docs(prompts): add operational discipline and superpowers guidelines to en prompt"
```

---

### Task 3: Update `SKILL.md` with Superpowers Synergy

**Files:**
- Modify: `SKILL.md`

**Interfaces:**
- Consumes: Existing skill workflow and safety boundary.
- Produces: Guidelines on how agents running with Superpowers (`using-superpowers`, `systematic-debugging`, `verification-before-completion`) should orchestrate this audit.

- [ ] **Step 1: Inspect target location in `SKILL.md`**
- [ ] **Step 2: Apply surgical diff using `replace_file_content` to add Superpowers integration guidelines**
- [ ] **Step 3: Verify skill metadata and markdown syntax**
- [ ] **Step 4: Commit changes**

```bash
git add SKILL.md
git commit -m "docs(skill): add superpowers orchestration and operational discipline guidelines"
```

---

### Task 4: Update `README.md` and `README.pt-BR.md`

**Files:**
- Modify: `README.md`
- Modify: `README.pt-BR.md`

**Interfaces:**
- Consumes: Agent skill installation and workflow sections.
- Produces: Updated documentation referencing [Superpowers](https://github.com/obra/superpowers) compatibility, agent discipline, and ecosystem synergy.

- [ ] **Step 1: Inspect target locations in both README files**
- [ ] **Step 2: Apply surgical diff to `README.md`**
- [ ] **Step 3: Apply surgical diff to `README.pt-BR.md`**
- [ ] **Step 4: Commit changes**

```bash
git add README.md README.pt-BR.md
git commit -m "docs: document superpowers compatibility and agent discipline"
```

---

### Task 5: Verification and Final Checks

**Files:**
- Test: `tests/`

- [ ] **Step 1: Run the test suite (`python -m unittest discover -s tests`)**
- [ ] **Step 2: Verify git status and diff integrity**
- [ ] **Step 3: Confirm all links to `https://github.com/obra/superpowers` resolve cleanly and no placeholders exist**
