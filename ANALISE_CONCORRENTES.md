# Análise de Concorrentes — BLI Legal Tech Hackathon 2 (DoraHacks)

> ⚠️ **SUPERSEDED — snapshot interno de 2026-10-20, NÃO é a leitura atual do campo.**
> Os números abaixo (53 dossiers, 129 testes) e as alegações de "único" estão desatualizados: os rivais atuais (Debate Desk, Bull v. Bear) desde então adicionaram âncora on-chain própria e a tag de spotlight multi-KOL. **A fonte de verdade atual é `scripts/enemy_watch.py` + `research/enemy-watch.json`** (roda a cada 3h no robô). Não use este arquivo para posicionamento público.

> **Data:** 2026-10-20
> **Referência:** Verdict Desk (nosso) — 53 dossiers, 129 testes, LLM Mistral, CRE workflow, dashboard visual, video demo, hash chain verificável, sensitivity analysis, audit-journal.
> **Deadline:** 31 out 2026 · **Prize pool:** ~$50K · **100+ projetos submetidos** (segundo BLI.Tools, out/2026)
> **Sponsors:** RYO Digital, Chainlink Labs

---

## 1. Sovereign LexGuard

| Campo | Detalhe |
|---|---|
| **Repo** | `github.com/SDRmsung/Sovereign-C-LexGuard-BLI` |
| **Status** | ✅ Ativo — submetido, testes passando (4/4 green < 3ms) |
| **Submetido** | ~29 ago 2026 |
| **Tracks** | RegTech, LegalTech, AI & Agents, RWA, Smart Contracts |

### Features
- **Formal SAT Solver (DPLL)** puro em Python — traduz estatutos legais para CNF e prova ausência de deadlocks
- **Su-Field Causal Model** — modela triângulos S₁/S₂/F para balançar direitos de liquidação vs. injunções judiciais
- **EIP-712 On-Chain Guard** — contrato `LexGuardCore.sol` verifica provas criptográficas off-chain antes de liquidar/transferir; atomic revert se conflito detectado
- **LegalDSLCompiler** — linguagem DSL legal → CNF
- **Zero dependências externas** (stdlib Python apenas)
- **CLI** `lexguard audit` para rodar verificações
- **Whitepaper + demo script 90s** incluídos

### Forças
- Abordagem matemática formal (SAT/DPLL) — diferencial forte contra alucinação de LLM
- Integração on-chain real (Solidity + EIP-712) — enforcement atomic
- Código limpo, testes instant, zero dependências — reproduzível por juízes
- Documentação extensa (whitepaper, submission form kit, demo script)

### Fraquezas
- **Sem UI/visual** — só CLI + testes; zero dashboard para juízes/usuários finais
- **Escopo limitado a RWA/DeFi** — não cobre pesquisa jurídica, due diligence, litigation
- **Sem chain verificável** de auditoria — o output é determinístico mas não há hash chain de evidência
- **Sem workflow CRE (Chainlink)** — apesar de ser hackathon com Chainlink como sponsor
- **Repo vazia** (0 stars, 0 forks) — pouca tração/comunidade
- **Sem sensitivity analysis** — não testa como variações de input afetam o resultado

### Ameaça: 🟡 MÉDIA
- O SAT solver é forte para compliance on-chain, mas não compete com o Verdict Desk no core (research + dossiers + CRE workflow + dashboard). Risco se o Verdict Desk for comparado no track de Smart Contracts.

### Como nos diferenciar
1. **Escopo amplo:** Verdict Desk cobre pesquisa jurídica, due diligence, litigation prep E compliance; LexGuard cobre só RWA/DeFi.
2. **CRE workflow:** Integrar Chainlink (sponsor do hackathon) para orquestração off-chain/on-chain — LexGuard não usa.
3. **Dashboard + demo visual:** Juízes veem UI funcional, não só CLI.
4. **Hash chain de auditoria:** Verdict Desk tem prova verificável de cada decisão; LexGuard tem prova SAT mas não cadeia de evidência.

---

## 2. PocketChange

| Campo | Detalhe |
|---|---|
| **Repo** | `github.com/Somay-kousis/Pocket-Change` |
| **Status** | ✅ Ativo — submetido 2/9, bounty Autonomous Agents |
| **Live Demo** | Cloud Run (asia-south1) |
| **Submetido** | ~2 set 2026 (repo criada) |
| **Commits** | 159 |

### Features
- **Capability tokens (Biscuit)** — delegação atenuável para agentes IA gastarem com limites
- **Funnel de decomposição** — tarefa recursiva gera 121-148 agentes com orçamentos hierárquicos
- **Monitor de segurança** — três verdicts: ALLOW / DEFER / ESCALATE
- **Ledger two-phase** com reservas (Firestore ou memory)
- **Hash-linked audit log** append-only
- **831 testes** (400 ataques adversariais)
- **Frontend com SSE** — 5 painéis live
- **Merchant adversarial** — simula 4 cenários maliciosos
- **Payouts reais** via Razorpay test mode

### Forças
- **Testes extensivos** — 831 testes incluindo 400 ataques, honestidade sobre bugs encontrados/corrigidos
- **Live demo funcional** — running no Cloud Run
- **Arquitetura madura** — separação trusted/untrusted, sibling vs child para prompt injection
- **Bounded spending** — problema real e bem resolvido para agentes autônomos
- **Documentação transparente** — post no DEV explicando bugs e correções

### Fraquezas
- **Foco em pagamentos de agentes**, não em legal tech propriamente dito
- **Razorpay (Índia)** — não é global, não serve compliance US/EU
- **Sem integração blockchain** — apesar do hackathon ser blockchain-focused
- **Sem análise jurídica** — nenhum componente de pesquisa legal, due diligence, ou compliance
- **Biscuit tokens** — interessante mas fora do escopo de legal tech
- **1 star, 1 fork** — mínima tração

### Ameaça: 🟢 BAIXA
- Problema adjacente (agent spending) mas não compete no mesmo espaço. Pode ganhar bounty de Autonomous Agents, mas não LegalTech/RegTech core.

### Como nos diferenciar
1. **Escopo legal:** Verdict Desk é ferramenta de legal research + compliance; PocketChange é wallet de agente.
2. **Chainlink CRE:** Verdict Desk usa o sponsor; PocketChange não toca blockchain.
3. **100+ testes + 53 dossiers** vs. 831 testes de pagamento — métricas diferentes, público diferente.

---

## 3. EvidenceTrail

| Campo | Detalhe |
|---|---|
| **Status** | ⚠️ DESAPARECIDO da DoraHacks (confirmado — "sumiu") |
| **EvidentTrail.com** | Site ativo — SOC 2 / ISO 27001 / EU AI Act compliance |
| **EvidenceTrail.co.uk** | Procurement pack (projeto diferente, UK social-landlord) |

### Features (conforme EvidentTrail.com — pode não ser o projeto do hackathon)
- **GitHub evidence capture** — PR approvals, branch protection, CI results
- **Tamper-evident packs** — SHA-256 checksums em evidências
- **AI-assisted code detection** — identifica co-authored-by, bot authors
- **Branch protection drift detection** — hash snapshots detectam mudanças silenciosas
- **Read-only GitHub App** — sem permissões de escrita
- **Export PDF/CSV/JSON** — evidence packs com checksums

### Forças (potenciais)
- Problema real de compliance (SOC 2, ISO 27001, EU AI Act)
- GitHub integration read-only é fácil de adotar
- AI awareness (detecção de código gerado por IA) é trending

### Fraquezas
- **Desapareceu da DoraHacks** — provavelmente desistiu ou foi desqualificado
- **Foco em DevSecOps**, não legal tech — é ferramenta de compliance de engenharia
- **Sem blockchain** — não toca os tracks do hackathon
- **Projeto pode ter sido dividido** — EvidentTrail.com (EUA) vs EvidenceTrail.co.uk (UK) são projetos distintos
- **Zero tração** — "First launch, no users yet" (segundo HN)

### Ameaça: 🟢 BAIXA (praticamente zero)
- Desaparecimento da plataforma sugere desistência ou falha em critérios. Mesmo se voltar, o foco é DevSecOps, não legal tech.

### Como nos diferenciar
- Verdict Desk nem precisa se preocupar com este — foco completamente diferente. Se ressurgir, destacar que nosso foco é legal research + compliance jurídico, não SDLC evidence.

---

## 4. PreTxSim

| Campo | Detalhe |
|---|---|
| **Repo** | `github.com/Skywalkingzulu1/bli-legaltech-pretctxsim` |
| **Status** | ⚠️ Em preparação — targeting BLI Hackathon, submissão ainda não confirmada |
| **Grant PR** | W3F Grants Program #2781 (Sep 23, 2026, 8/9 reviews) |
| **Stack** | Rust, `revm`, Ollama (`smollm2`) |

### Features
- **Air-gapped local EVM simulation proxy** — intercepta `eth_sendTransaction`, simula antes de broadcast
- **revm deterministic simulation** — replay contra live RPC state (balance deltas, gas, slippage)
- **Local LLM auditor** — Ollama `smollm2` para PASS/WARN, zero data leaving machine
- **RiskInspector** — flags delegatecalls, selfdestructs, storage writes, EIP-7702
- **The Gate** — interactive refuse/accept antes de broadcast
- **RPC proxy form factor** — drop-in em `127.0.0.1:8545`
- **<800MB footprint** — enterprise/compliance posture

### Forças
- **Rust + revm** — performance e segurança fortes
- **Air-gapped** — privacidade total, nenhuma chave sai da máquina
- **Drop-in proxy** — zero integração, funciona com qualquer wallet/bot/agent
- **Local LLM** — sem dependência de API externa, compliance-friendly
- **Multi-hackathon** — targeting 12 eventos simultaneamente (estratégia agressiva)

### Fraquezas
- **Submissão ainda não confirmada** na DoraHacks (em fase de preparação)
- **Foco em segurança de transação**, não em legal research/compliance jurídico
- **Pitch split em 12 hackathons** — pode parecer genérico/diluído
- **Sem workflow de pesquisa jurídica** — não analisa estatutos, casos, contratos
- **LLM local pequeno** (`smollm2`) — capacidade limitada de raciocínio legal
- **Sem dashboard, sem demo visual, sem hash chain de evidência**

### Ameaça: 🟡 MÉDIA-BAIXA
- Se submeter, compete no track de RegTech (pre-execution verification against compliance policy). Mas o core é security tool, não legal tech. Risco se a narrativa de "compliance pré-transação" ressoar com juízes.

### Como nos diferenciar
1. **Legal research completo:** Verdict Desk analisa estatutos, precedentes, contratos; PreTxSim simula transações EVM.
2. **CRE + Chainlink:** Verdict Desk usa o sponsor principal; PreTxSim é independente.
3. **53 dossiers + 129 testes** vs. simulação EVM — domínios diferentes.
4. **Dashboard visual + video demo** — PreTxSim tem ASCII/Mermaid e GIF.
5. **Sensitivity analysis + audit-journal** — PreTxSim não tem.

---

## Resumo Comparativo

| Projeto | Status | Core | Threat | vs. Verdict Desk |
|---|---|---|---|---|
| **Sovereign LexGuard** | ✅ Submetido | SAT solver + EIP-712 on-chain guard | 🟡 MÉDIA | Forte em compliance on-chain; fraco em UI, escopo, CRE |
| **PocketChange** | ✅ Submetido (2/9) | Bounded spending + Biscuit tokens p/ agentes IA | 🟢 BAIXA | Problema adjacente, não compete em legal tech |
| **EvidenceTrail** | ⚠️ Desaparecido | GitHub evidence p/ SOC2/ISO27001 | 🟢 BAIXA | Foco DevSecOps, provavelmente fora |
| **PreTxSim** | ⚠️ Em prep. | EVM simulation proxy + local LLM auditor | 🟡 MÉDIA-BAIXA | Security tool, não legal research; pode competir em RegTech |

---

## Vantagens Estratégicas do Verdict Desk

1. **Escopo completo:** Único projeto cobrindo pesquisa jurídica, due diligence, litigation prep E compliance — competidores cobrem fatias isoladas
2. **CRE workflow com Chainlink:** Usa o sponsor principal do hackathon; nenhum concorrente identificado integra Chainlink
3. **53 dossiers + 129 testes:** Volume e profundidade de testes inigualáveis
4. **Dashboard visual + video demo:** Juízes veem produto funcionando, não CLI ou README
5. **Hash chain verificável:** Prova de integridade de cada decisão — único com audit trail criptográfico
6. **Sensitivity analysis:** Testa robustez de conclusões sob variação de parâmetros — nenhum concorrente tem
7. **Audit-journal:** Registro imutável de todas as operações
8. **LLM Mistral:** Modelo open-source, sem dependência de API proprietária

## Riscos a Monitorar

- **Novas submissões na última semana:** Deadline 31/out — 100+ projetos, muitos podem submeter no final
- **Sovereign LexGuard** pode pivotar para adicionar UI ou CRE antes do deadline
- **PreTxSim** pode confirmar submissão e ganhar tração no track de RegTech
- **Projetos não encontrados** — a página de buidls no DoraHacks requer login para listagem completa; podem existir competidores fortes não indexados na web pública

## Recomendações

1. **Reforçar narrativa Chainlink CRE** — é o sponsor, nenhum concorrente usa
2. **Destacar volume de testes (129)** — métrica concreta que juízes podem verificar
3. **Video demo forte** — único projeto com UI visual entre os identificados
4. **Monitorar DoraHacks diariamente** até 31/out para novas submissões relevantes
5. **Preparar resposta para LexGuard** — se questionado sobre compliance on-chain, enfatizar que Verdict Desk cobre o pipeline completo (research → análise → compliance → auditoria), não só a verificação on-chain
