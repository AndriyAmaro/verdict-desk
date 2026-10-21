#!/usr/bin/env node
// Checks what the LedgerAnchor contract on Sepolia holds against the public ledger. Read-only: no key needed.
//
//   node cre/contracts/scripts/check-anchor.mjs                      # address from anchor/config.staging.json
//   node cre/contracts/scripts/check-anchor.mjs --address 0x... --ledger https://andriyamaro.github.io/verdict-desk/ledger/ledger.jsonl
//
// It (1) verifies the whole hash chain of the ledger with the same code the dashboard runs, (2) reads the
// latest anchored sequence number and head hash from the contract, (3) asks the contract `isAnchored(seq, hash)`
// for the hash this ledger has at that sequence number, and (4) finds the transaction that anchored it.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import { createPublicClient, getAddress, http, isAddress, zeroAddress } from 'viem'
import { sepolia } from 'viem/chains'

const here = path.dirname(fileURLToPath(import.meta.url))
const cre = path.join(here, '..', '..')
const { verifyLedger } = createRequire(import.meta.url)(path.join(cre, '..', 'web', 'canonical.js'))

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`)
  return i >= 0 && process.argv[i + 1] && !process.argv[i + 1].startsWith('--') ? process.argv[i + 1] : fallback
}
const fail = (message, code = 1) => { console.error(`error: ${message}`); process.exit(code) }

const config = JSON.parse(fs.readFileSync(path.join(cre, 'anchor', 'config.staging.json'), 'utf8'))
const address = arg('address', config.anchorAddress)
if (!isAddress(address) || address === zeroAddress) fail('no LedgerAnchor address yet: pass --address or set anchorAddress in cre/anchor/config.staging.json', 2)
const rpc = arg('rpc', process.env.SEPOLIA_RPC_URL || 'https://ethereum-sepolia-rpc.publicnode.com')
const ledgerSource = arg('ledger', path.join(cre, '..', 'ledger', 'ledger.jsonl'))
const abi = JSON.parse(fs.readFileSync(path.join(cre, 'contracts', 'evm', 'src', 'abi', 'LedgerAnchor.abi'), 'utf8'))

const text = /^https?:\/\//.test(ledgerSource) ? await (await fetch(ledgerSource)).text() : fs.readFileSync(ledgerSource, 'utf8')
const chain = await verifyLedger(text, async (t) => crypto.createHash('sha256').update(t).digest('hex'))
console.log(`ledger ${ledgerSource}: ${chain.rows.length} dossiers, chain ${chain.problems.length ? 'BROKEN: ' + chain.problems.join('; ') : 'intact (every hash recomputed here)'}`)

const client = createPublicClient({ chain: sepolia, transport: http(rpc) })
if ((await client.getChainId()) !== 11155111) fail(`${rpc} is not Ethereum Sepolia`)
const read = (functionName, args = []) => client.readContract({ address, abi, functionName, args })
const latestSeq = await read('latestSeq')
if (latestSeq === 0n) fail(`contract ${address} has anchored nothing yet`, 2)
const [headHash, price, decimals, priceUpdatedAt, anchoredAt] = await read('anchors', [latestSeq])
console.log(`contract ${getAddress(address)} on Sepolia: latest anchored seq ${latestSeq}, head hash ${headHash.slice(2)}`)
console.log(`  Data Feed price recorded with it: ${Number(price) / 10 ** decimals} (feed updated ${new Date(Number(priceUpdatedAt) * 1000).toISOString()}), anchored at ${new Date(Number(anchoredAt) * 1000).toISOString()}`)

const row = chain.rows.find((r) => BigInt(r.dossier.seq) === latestSeq)
let match = false
if (!row) {
  console.log(`  this ledger has no dossier with seq ${latestSeq}`)
} else {
  match = await read('isAnchored', [latestSeq, `0x${row.dossier.hash}`])
  console.log(`  dossier ${row.dossier.seq} in this ledger has hash ${row.dossier.hash}`)
  console.log(`  isAnchored(${latestSeq}, hash) on-chain: ${match ? 'TRUE: the anchored head is exactly this dossier' : 'FALSE: the ledger differs from what was anchored'}`)
}

const logs = await client.getLogs({ address, event: abi.find((e) => e.type === 'event' && e.name === 'Anchored'), args: { seq: latestSeq }, fromBlock: BigInt(Math.max(0, Number(await client.getBlockNumber()) - 40000)) })
if (logs.length) console.log(`  anchoring transaction: https://sepolia.etherscan.io/tx/${logs[logs.length - 1].transactionHash}`)
process.exit(chain.problems.length === 0 && match ? 0 : 1)
