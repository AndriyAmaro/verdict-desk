import { describe, expect } from 'bun:test'
import { TxStatus } from '@chainlink/cre-sdk'
import { EvmMock, newTestRuntime, REPORT_METADATA_HEADER_LENGTH, test } from '@chainlink/cre-sdk/test'
import { bytesToHex, type Address } from 'viem'
import { newAggregatorV3Mock } from '../contracts/evm/ts/generated/AggregatorV3_mock'
import { newLedgerAnchorMock } from '../contracts/evm/ts/generated/LedgerAnchor_mock'
import { decodeAnchorReport } from './logic'
import { anchorLedger, type Config, initWorkflow, onCronTrigger } from './workflow'

const SEPOLIA_SELECTOR = 16015286601757825753n // ethereum-testnet-sepolia
const FEED = '0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43' as Address
const ANCHOR = '0x00000000000000000000000000000000000a11c0' as Address
const HASH = 'ab'.repeat(32)
const HEAD = { seq: 12, hash: HASH, symbol: 'BTCUSDT' }

const config: Config = {
	schedule: '0 0 0 * * *',
	headUrl: 'https://example.invalid/head.json',
	chainSelectorName: 'ethereum-testnet-sepolia',
	priceFeedAddress: FEED,
	anchorAddress: ANCHOR,
	gasLimit: '500000',
}

function mocks(txStatus: TxStatus = TxStatus.SUCCESS) {
	const evm = EvmMock.testInstance(SEPOLIA_SELECTOR)
	const feed = newAggregatorV3Mock(FEED, evm)
	feed.decimals = () => 8
	feed.latestRoundData = () => [1n, 6_700_012_345_678n, 1_759_999_000n, 1_760_000_000n, 1n]
	const anchor = newLedgerAnchorMock(ANCHOR, evm)
	const seen: Array<{ receiver: string; payload: Uint8Array; gasLimit: string }> = []
	anchor.writeReport = (input) => {
		seen.push({
			receiver: bytesToHex(input.receiver),
			payload: input.report.rawReport.slice(REPORT_METADATA_HEADER_LENGTH),
			gasLimit: String(input.gasConfig.gasLimit),
		})
		return { txStatus, txHash: new Uint8Array(32).fill(7) } as never // the mock accepts the plain JSON shape of the reply
	}
	return seen
}

describe('anchorLedger', () => {
	test('reads the Data Feed and sends the ledger head and price to LedgerAnchor', () => {
		const seen = mocks()
		const runtime = newTestRuntime(null, undefined, config)
		const summary = JSON.parse(anchorLedger(runtime, HEAD))

		expect(summary).toMatchObject({ seq: 12, head: HASH, symbol: 'BTCUSDT', price: '67000.12345678' })
		expect(seen).toHaveLength(1)
		expect(seen[0].receiver.toLowerCase()).toBe(ANCHOR.toLowerCase())
		expect(seen[0].gasLimit).toBe('500000')
		expect(decodeAnchorReport(bytesToHex(seen[0].payload))).toEqual({
			seq: 12n,
			headHash: `0x${HASH}`,
			price: 6_700_012_345_678n,
			decimals: 8,
			priceUpdatedAt: 1_760_000_000n,
		})
	})

	test('fails loudly when the forwarder reports a failed transaction', () => {
		mocks(TxStatus.REVERTED)
		expect(() => anchorLedger(newTestRuntime(null, undefined, config), HEAD)).toThrow('failed to write report')
	})

	test('refuses to anchor a non-positive Data Feed answer', () => {
		const evm = EvmMock.testInstance(SEPOLIA_SELECTOR)
		const feed = newAggregatorV3Mock(FEED, evm)
		feed.decimals = () => 8
		feed.latestRoundData = () => [1n, 0n, 0n, 0n, 1n]
		newLedgerAnchorMock(ANCHOR, evm).writeReport = () => ({ txStatus: TxStatus.SUCCESS }) as never
		expect(() => anchorLedger(newTestRuntime(null, undefined, config), HEAD)).toThrow('price feed answer must be positive')
	})
})

describe('onCronTrigger', () => {
	test('requires the scheduled execution time', () => {
		expect(() => onCronTrigger(newTestRuntime(null, undefined, config), {} as any)).toThrow('scheduled execution time is required')
	})
})

describe('initWorkflow', () => {
	test('subscribes onCronTrigger to the configured schedule', () => {
		const handlers = initWorkflow(config)
		expect(handlers).toHaveLength(1)
		expect(handlers[0].fn).toBe(onCronTrigger)
		expect((handlers[0].trigger as { config?: { schedule?: string } }).config?.schedule).toBe(config.schedule)
	})
})
