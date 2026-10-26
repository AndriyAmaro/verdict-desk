#!/usr/bin/env node
// Sends one practice trade (or receipt) to PracticeDesk on Sepolia and prints the result as one JSON line.
// Called by verdict_desk/practice.py inside the hourly run; the key comes from SEPOLIA_PRIVATE_KEY and is never printed.
//
//   node practice.mjs '{"kind":"open","seq":380,"symbol":"ETHUSDT","side":"short","market":"WETH/USDC","decision":"0x…","weth":0.002}'
//
// ETHUSDT (market WETH/USDC): open SHORT sells `weth` WETH for test USDC; open LONG buys `weth` WETH with test USDC at
// the pool's price; close spends `amount_in` of `token_in` (what the opening received). Other symbols: a receipt only.
// Never throws: any failure is printed as {"status":"failed","error":…} so the decision is still recorded.
import fs from 'node:fs'
import { decodeEventLog, parseEther, toHex } from 'viem'
import { clients, DEPLOYMENT, deskAbi, SEPOLIA, usdcPerWeth } from './practice-common.mjs'

const KIND = { open: 0, close: 1 }
const SIDE = { long: 1, short: 2 }
const print = (o) => console.log(JSON.stringify(o))

async function main() {
  const req = JSON.parse(process.argv[2] || '{}')
  if (!(req.kind in KIND) || !(req.side in SIDE) || !/^0x[0-9a-f]{64}$/.test(req.decision || '')) throw new Error('bad request')
  const desk = JSON.parse(fs.readFileSync(DEPLOYMENT, 'utf8')).contract
  const { account, pub, wallet } = clients()
  const abi = deskAbi()
  const base = [BigInt(req.seq), req.decision, KIND[req.kind], SIDE[req.side]]
  let functionName, args, price = null
  if (req.market === 'WETH/USDC') {
    price = await usdcPerWeth(pub)
    let tokenIn, amountIn
    if (req.kind === 'close') {
      if (!req.amount_in) throw new Error('close needs amount_in')
      tokenIn = req.token_in === 'usdc' ? SEPOLIA.usdc : SEPOLIA.weth
      amountIn = BigInt(req.amount_in)
    } else if (req.side === 'short') {
      tokenIn = SEPOLIA.weth
      amountIn = parseEther(String(req.weth))
    } else {
      tokenIn = SEPOLIA.usdc
      amountIn = BigInt(Math.round(req.weth * price * 1e6))
    }
    const tokenOut = tokenIn === SEPOLIA.weth ? SEPOLIA.usdc : SEPOLIA.weth
    functionName = 'trade'
    args = [...base, tokenIn, tokenOut, SEPOLIA.fee, amountIn, 1n]
  } else {
    functionName = 'record'
    args = [...base, toHex(String(req.symbol).slice(0, 32), { size: 32 })]
  }
  if (req.dry_run) {
    // eth_call only: proves the whole path against Sepolia without writing a receipt
    const { result } = await pub.simulateContract({ account, address: desk, abi, functionName, args })
    print({ status: 'dry-run', function: functionName, amount_in: functionName === 'trade' ? args[7].toString() : null,
      amount_out: result === undefined ? null : result.toString(), testnet_usdc_per_weth: price === null ? null : Math.round(price) })
    return
  }
  let hash
  for (let attempt = 0; ; attempt++) {
    try {
      const { request } = await pub.simulateContract({ account, address: desk, abi, functionName, args })
      hash = await wallet.writeContract(request)
      break
    } catch (err) {
      // the anchor shares this wallet: one retry on a nonce clash, nothing else is retried
      if (attempt === 0 && /nonce/i.test(String(err.shortMessage || err.message))) continue
      throw err
    }
  }
  const receipt = await pub.waitForTransactionReceipt({ hash })
  if (receipt.status !== 'success') throw new Error(`transaction reverted: ${hash}`)
  const out = { status: functionName === 'trade' ? 'executed' : 'recorded', tx: hash, block: Number(receipt.blockNumber) }
  for (const log of receipt.logs) {
    try {
      const ev = decodeEventLog({ abi, data: log.data, topics: log.topics })
      if (ev.eventName === 'PracticeTrade') {
        Object.assign(out, { token_in: ev.args.tokenIn, token_out: ev.args.tokenOut, amount_in: ev.args.amountIn.toString(), amount_out: ev.args.amountOut.toString() })
      }
    } catch {
      // logs of the tokens and the pool, not the desk's
    }
  }
  if (price !== null) out.testnet_usdc_per_weth = Math.round(price)
  print(out)
}

main().catch((err) => {
  print({ status: 'failed', error: String(err.shortMessage || err.message || err).slice(0, 300) })
})
