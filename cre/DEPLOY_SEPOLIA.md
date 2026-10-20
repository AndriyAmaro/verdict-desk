# Verdict Desk CRE — Sepolia Deploy Guide

## Status atual (2026-10-20)

| Peça | Status |
|---|---|
| `logic.ts` (pure functions) | ✅ 5/5 unit tests pass |
| `workflow.ts` (handler) | ✅ 5/5 workflow tests pass |
| `LedgerAnchor.sol` | ✅ 6/6 EVM contract tests pass |
| `bunx tsc --noEmit` | ✅ clean |
| `cre workflow simulate` | ⏳ bloqueado por falta de `CRE_API_KEY` (Andri precisa logar) |
| Deploy Sepolia | ⏳ pendente |

---

## 1. Pré-requisitos

### Conta Chainlink CRE
1. Criar conta em https://app.chain.link
2. Ir em **Account Settings → API Keys** e gerar uma chave
3. No terminal: `export CRE_API_KEY=<sua-chave>` ou rodar `cre login` (abre browser)

### Faucet Sepolia (ETH testnet)
Para deploy do contrato e futuras transações com `--broadcast`, precisa de ETH Sepolia:
- **Chainlink Faucet**: https://faucets.chain.link/sepolia (precisa conectar wallet com ≥0.001 ETH mainnet)
- **Google Cloud Faucet**: https://cloud.google.com/application/web3/faucet/ethereum/sepolia
- **Alchemy Faucet**: https://sepoliafaucet.com/
- **Sepolia PoW Faucet**: https://sepolia-faucet.pk910.de/ (minerar, sem requisitos)

> **Quantidade necessária**: ~0.05 ETH Sepolia cobre deploy do contrato + várias simulações com `--broadcast`.

### Ferramentas instaladas (já verificadas)
- ✅ CRE CLI v1.38.0 (`~/.cre/bin/cre`)
- ✅ Bun 1.4.3
- ✅ `bun install` em `cre/anchor/` — 49 pacotes
- ✅ `npm install` em `cre/contracts/evm/` (viem + cre-sdk adicionados para resolver bindings)

---

## 2. Rodar a simulação (próximo passo)

```bash
cd /tmp/verdict-desk-work

# Opção A: login interativo (abre browser)
~/.cre/bin/cre login

# Opção B: variável de ambiente (CI/automatizado)
export CRE_API_KEY="ck_..."

# Simulação (sem broadcast)
~/.cre/bin/cre workflow simulate cre/anchor --target staging-settings

# Com broadcast (escreve no contrato real na Sepolia)
~/.cre/bin/cre workflow simulate cre/anchor --target staging-settings --broadcast
```

### O que a simulação faz
1. Compila o workflow TypeScript → WASM
2. Executa o trigger cron (simula uma execução agendada)
3. Faz GET no `headUrl` (`ledger/head.json` do GitHub)
4. Lê o Data Feed BTC/USD da Chainlink em Sepolia
5. Codifica o report e simula a chamada `LedgerAnchor.writeReport()`
6. Retorna o resultado sem escrever na blockchain (sem `--broadcast`)

---

## 3. Deploy do contrato LedgerAnchor em Sepolia

### Passo 3.1: Descobrir endereços do Forwarder

Antes de deployar, confirmar os endereços no **CRE Forwarder Directory**:
https://docs.chain.link/cre

| Forwarder | Endereço (verificar!) | Uso |
|---|---|---|
| MockKeystoneForwarder (simulação) | `0x15fc6ae953e024d975e77382eeec56a9101f9f88` | Para testar antes de deployar workflow real |
| CRE Forwarder (produção) | `0xf8344cfd5c436616a4366c34e3eee75af79a74482` | Para workflow publicado no Chainlink Cloud |

### Passo 3.2: Deploy do contrato

```bash
cd /tmp/verdict-desk-work/cre/contracts/evm

# Compilar (gera ABI + bytecode)
npm run compile

# Deploy via cast (foundry) ou forge, ou script customizado
# O construtor é: LedgerAnchor(address forwarder, address expectedWorkflowOwner)
```

**Parâmetros do construtor:**
- `forwarder`: endereço do CRE Forwarder (MockKeystone ou produção)
- `expectedWorkflowOwner`: endereço da conta CRE que será dona do workflow

**Exemplo com `cast` (Foundry):**
```bash
# Instalar foundry se não tiver
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Deploy
cast create \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com \
  --private-key $SEPOLIA_PRIVATE_KEY \
  --constructor-args "0x15fc6ae953e024d975e77382eeec56a9101f9f88 0xSeuEnderecoCRE" \
  $(cat build/LedgerAnchor.bin)
```

### Passo 3.3: Atualizar config.staging.json

Após deploy, atualizar `anchorAddress` no `cre/anchor/config.staging.json`:

```json
{
  "anchorAddress": "0x<ENDEREÇO_DO_CONTRATO_DEPLOYADO>",
  "priceFeedAddress": "0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43",
  "chainSelectorName": "ethereum-testnet-sepolia",
  "headUrl": "https://raw.githubusercontent.com/AndriyAmaro/verdict-desk/main/ledger/head.json",
  "schedule": "0 0 0 * * *",
  "gasLimit": "500000"
}
```

### Passo 3.4: Verificar na blockchain

```bash
# Verificar que o contrato está lá
cast code <ENDEREÇO_DO_CONTRATO> --rpc-url https://ethereum-sepolia-rpc.publicnode.com

# Chamar isAnchored para verificar
# (precisa da ABI e do seq/hash esperado)
```

---

## 4. Checklist final

- [ ] `cre login` ou `CRE_API_KEY` exportada
- [ ] `cre workflow simulate cre/anchor --target staging-settings` passa
- [ ] ETH Sepolia na wallet (faucet)
- [ ] Forwarder Directory confirmado (endereços válidos)
- [ ] `LedgerAnchor` deployado em Sepolia
- [ ] `config.staging.json` com `anchorAddress` real
- [ ] `cre workflow simulate ... --broadcast` executa com sucesso
- [ ] `isAnchored(seq, hash)` retorna true on-chain

---

## Referência rápida de endereços

| Recurso | Endereço |
|---|---|
| BTC/USD Data Feed Sepolia | `0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43` |
| MockKeystoneForwarder Sepolia | `0x15fc6ae953e024d975e77382eeec56a9101f9f88` |
| CRE Forwarder Sepolia | `0xf8344cfd5c436616a4366c34e3eee75af79a74482` |
| RPC Sepolia (público) | `https://ethereum-sepolia-rpc.publicnode.com` |
| Ledger head (live) | https://raw.githubusercontent.com/AndriyAmaro/verdict-desk/main/ledger/head.json |
