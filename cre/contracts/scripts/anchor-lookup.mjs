// Finds the transaction that emitted the `Anchored` event for a sequence number, without asking a public RPC for
// more log history than it keeps. Free Sepolia endpoints answer "pruned history unavailable" to a wide range, so the
// search walks backwards from the newest block in small windows and stops at the block the contract was deployed in.
//
// The function never throws: a node that cannot serve the logs yields `{ tx: null, note }` with the reason, and the
// caller prints it next to the verdict (the verdict itself comes from state reads, not from this search).

export const WINDOW_BLOCKS = 5000n
export const DEFAULT_LOOKBACK_BLOCKS = 200000n

/**
 * @param {object} options
 * @param {{ getBlockNumber(): Promise<bigint>, getLogs(args: object): Promise<Array<{ transactionHash: string }>> }} options.client
 * @param {string} options.address contract address
 * @param {object} options.event ABI item of the `Anchored` event
 * @param {bigint} options.seq sequence number to look for (indexed argument `seq`)
 * @param {bigint | null} [options.floorBlock] never search below this block (the deployment block, when known)
 * @param {bigint} [options.window] blocks per request
 */
export async function findAnchoringTx({ client, address, event, seq, floorBlock = null, window = WINDOW_BLOCKS }) {
  let latest
  try {
    latest = await client.getBlockNumber()
  } catch (error) {
    return { tx: null, note: `the RPC did not answer the block number request (${reason(error)})` }
  }
  const floor = floorBlock ?? (latest > DEFAULT_LOOKBACK_BLOCKS ? latest - DEFAULT_LOOKBACK_BLOCKS : 0n)
  let to = latest
  while (to >= floor) {
    const from = to - window + 1n > floor ? to - window + 1n : floor
    let logs
    try {
      logs = await client.getLogs({ address, event, args: { seq }, fromBlock: from, toBlock: to })
    } catch (error) {
      const covered = to < latest ? ` Blocks ${to + 1n} to ${latest} had no such event.` : ''
      return {
        tx: null,
        note: `the RPC could not serve the logs for blocks ${from} to ${to} (${reason(error)}).${covered} Set SEPOLIA_RPC_URL to an endpoint with full log history, or open the contract on Etherscan`,
      }
    }
    if (logs.length) return { tx: logs[logs.length - 1].transactionHash, note: null }
    if (from === floor) break
    to = from - 1n
  }
  return { tx: null, note: `no Anchored event for sequence number ${seq} between blocks ${floor} and ${latest}` }
}

function reason(error) {
  return String((error && (error.details || error.shortMessage || error.message)) || error).split('\n')[0]
}
