# 🎬 VERDICT DESK — DEMO V3 SCRIPT (Final)

## Status Atual (20/10/2026, 17:20)

| Métrica | Valor |
|---|---|
| **Dossiers no ledger** | 56 (crescendo hourly) |
| **Testes** | 129/129 passando ✅ |
| **Hash chain** | INTACT ✅ |
| **Replay** | 54 MATCHES, 0 DIFFERS ✅ |
| **LLM debate** | Working (3 accepted no seq 46) ✅ |
| **decide-v2** | LONG com edge 2.5 ✅ |
| **CRE workflow** | Compilado, simulando ⏳ |

---

## 📹 Opção 1: Gravação Automatizada (RECOMENDADA)

Rode este script e grave a tela:

```bash
cd /tmp/verdict-desk-work
bash RECORD_DEMO.sh
```

**O que o script faz:**
1. Mostra git log e ledger (setup)
2. Roda `decide BTCUSDT` (v1 + v2)
3. Mostra LLM debate do dossier #46
4. Roda `verify` (hash chain)
5. Roda `replay` (todas decisões)
6. Roda `portfolio` (posições simuladas)
7. Abre dashboard no browser
8. Mostra estrutura CRE
9. Roda 129 testes

**Tempo estimado:** ~4 minutos

---

## 📹 Opção 2: Demo Automatizada (texto)

Rode este script para gerar output completo:

```bash
cd /tmp/verdict-desk-work
python3 AUTO_DEMO.py
```

**Output:** `web/demo/auto-demo-output.txt` com todos os resultados.

---

## 📝 Narrativa Sugerida (para voz)

> "Verdict Desk is an audit-grade, replayable AI decision system for market analysis.
> 
> It freezes public market evidence — candles from Binance, funding from OKX, news from GDELT — into immutable packets. Then a bull agent and a bear agent debate over the same evidence, with each claim required to cite specific evidence items. A deterministic judge weighs the arguments and sizes a simulated position.
> 
> Every decision becomes a dossier, hash-chained to the previous one. The resulting ledger is a public, tamper-evident audit trail that anyone can verify in their browser.
> 
> For the Chainlink CRE bounty, there's a workflow that anchors the ledger head on-chain — fetching the public ledger, reading the BTC/USD Data Feed on Sepolia, and writing both to a contract.
> 
> 129 tests pass. 56 dossiers in the live ledger. All replays match. The code is Python stdlib only — zero dependencies."

---

## ✅ Checklist Final

- [x] Código funcionando (129 testes)
- [x] LLM debate operational (seq 46+)
- [x] Hash chain verificável
- [x] Replay 100% matches
- [x] Dashboard visual
- [x] CRE workflow compilado
- [x] Draft de submissão pronto
- [x] Script de gravação pronto
- [ ] Video gravado (você faz)
- [ ] Build page DoraHacks completa (você faz)
- [ ] Submissão enviada (você faz)

---

## 📁 Arquivos Gerados

| Arquivo | Descrição |
|---|---|
| `RECORD_DEMO.sh` | Script de gravação passo-a-passo |
| `AUTO_DEMO.py` | Demo automatizada com outputs |
| `VIDEO_SCRIPT.md` | Roteiro detalhado (267 linhas) |
| `SUBMISSAO_DORAHACKS.md` | Draft da submissão (188 linhas) |
| `ANALISE_CONCORRENTES.md` | Análise de competidores |
| `web/demo/auto-demo-output.txt` | Outputs da demo automatizada |
