// Checks cre/contracts/scripts/anchor-lookup.mjs with a fake client (no network, no viem). Run by tests/test_anchor_lookup.py.
import assert from 'node:assert/strict'
import { DEFAULT_LOOKBACK_BLOCKS, findAnchoringTx, WINDOW_BLOCKS } from '../cre/contracts/scripts/anchor-lookup.mjs'

const address = '0x50443D51Db71A61E131B147B1d36aF21d48CDdF7'
const event = { type: 'event', name: 'Anchored' }

// A client whose logs come from a table of { block, tx }; it records every getLogs request.
function client({ latest, logs = [], failAt = null, failBlockNumber = false }) {
  const requests = []
  return {
    requests,
    async getBlockNumber() {
      if (failBlockNumber) throw new Error('boom\nsecond line')
      return latest
    },
    async getLogs({ address: a, args, fromBlock, toBlock }) {
      requests.push({ address: a, seq: args.seq, fromBlock, toBlock })
      if (failAt !== null && requests.length === failAt) {
        const error = new Error('RPC Request failed.')
        error.details = 'pruned history unavailable'
        throw error
      }
      return logs.filter((l) => l.block >= fromBlock && l.block <= toBlock).map((l) => ({ transactionHash: l.tx }))
    },
  }
}
const run = (c, extra = {}) => findAnchoringTx({ client: c, address, event, seq: 80n, ...extra })
const done = []
const check = async (name, body) => { await body(); done.push(name); console.log(`ok  ${name}`) }

await check('a recent event is found in the first window', async () => {
  const c = client({ latest: 11_964_100n, logs: [{ block: 11_964_023n, tx: '0xabc' }] })
  const r = await run(c, { floorBlock: 11_963_992n })
  assert.deepEqual(r, { tx: '0xabc', note: null })
  assert.equal(c.requests.length, 1)
  assert.equal(c.requests[0].toBlock, 11_964_100n)
  assert.equal(c.requests[0].fromBlock, 11_963_992n)  // the whole range since deployment is smaller than one window
  assert.equal(c.requests[0].seq, 80n)
  assert.equal(c.requests[0].address, address)
})

await check('empty windows are walked backwards without gaps or overlaps', async () => {
  const latest = 100_000n
  const c = client({ latest, logs: [{ block: latest - 2n * WINDOW_BLOCKS - 17n, tx: '0xdeep' }] })
  const r = await run(c, { floorBlock: 0n })
  assert.equal(r.tx, '0xdeep')
  assert.equal(c.requests.length, 3)
  assert.equal(c.requests[0].toBlock, latest)
  for (let i = 1; i < c.requests.length; i++) assert.equal(c.requests[i].toBlock, c.requests[i - 1].fromBlock - 1n)
  for (const q of c.requests) assert.ok(q.toBlock - q.fromBlock + 1n <= WINDOW_BLOCKS)
})

await check('the search never goes below the floor and says nothing was found', async () => {
  const c = client({ latest: 1200n })
  const r = await run(c, { floorBlock: 1000n })
  assert.equal(r.tx, null)
  assert.match(r.note, /no Anchored event for sequence number 80 between blocks 1000 and 1200/)
  assert.deepEqual(c.requests.map((q) => [q.fromBlock, q.toBlock]), [[1000n, 1200n]])
})

await check('windows end exactly on the floor', async () => {
  const floor = 100n
  const latest = floor + 2n * WINDOW_BLOCKS - 1n
  const c = client({ latest })
  await run(c, { floorBlock: floor })
  assert.deepEqual(c.requests.map((q) => [q.fromBlock, q.toBlock]), [[latest - WINDOW_BLOCKS + 1n, latest], [floor, latest - WINDOW_BLOCKS]])
})

await check('without a floor the look-back is bounded', async () => {
  const latest = 1_000_000n
  const c = client({ latest })
  await run(c)
  const lowest = c.requests[c.requests.length - 1].fromBlock
  assert.equal(lowest, latest - DEFAULT_LOOKBACK_BLOCKS)
})

await check('a node that pruned the history gives a note, not an exception', async () => {
  const c = client({ latest: 50_000n, failAt: 1 })
  const r = await run(c, { floorBlock: 0n })
  assert.equal(r.tx, null)
  assert.match(r.note, /pruned history unavailable/)
  assert.match(r.note, /SEPOLIA_RPC_URL/)
})

await check('a failure after empty windows says which blocks were covered', async () => {
  const c = client({ latest: 50_000n, failAt: 2 })
  const r = await run(c, { floorBlock: 0n })
  assert.equal(r.tx, null)
  assert.match(r.note, /Blocks 45001 to 50000 had no such event/)
})

await check('a node that does not answer the block number gives a note too', async () => {
  const r = await run(client({ latest: 0n, failBlockNumber: true }))
  assert.equal(r.tx, null)
  assert.match(r.note, /did not answer the block number request \(boom\)/)
})

await check('several events in one window: the newest transaction wins', async () => {
  const c = client({ latest: 2000n, logs: [{ block: 1500n, tx: '0xold' }, { block: 1900n, tx: '0xnew' }] })
  const r = await run(c, { floorBlock: 1000n })
  assert.equal(r.tx, '0xnew')
})

console.log(`all ok (${done.length} checks)`)
