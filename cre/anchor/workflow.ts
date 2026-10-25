import {
	bytesToHex,
	consensusIdenticalAggregation,
	type CronPayload,
	cre,
	getNetwork,
	type HTTPSendRequester,
	type Runtime,
	TxStatus,
} from '@chainlink/cre-sdk'
import type { Address } from 'viem'
import { z } from 'zod'
import { AggregatorV3 } from '../contracts/evm/ts/generated/AggregatorV3'
import { LedgerAnchor } from '../contracts/evm/ts/generated/LedgerAnchor'
import { agreeOnHead, encodeAnchorReport, formatPrice, type LedgerHead, parseHead } from './logic'

export const configSchema = z.object({
	// 6-field cron (seconds first), e.g. "0 0 0 * * *" for daily at 00:00 UTC
	schedule: z.string(),
	// Public URL of the ledger head JSON written by `python -m verdict_desk head`
	headUrl: z.string(),
	// A second, independent publication of the same head (the GitHub Pages site, not the raw repository file)
	headUrlMirror: z.string(),
	chainSelectorName: z.string(),
	priceFeedAddress: z.string(),
	anchorAddress: z.string(),
	gasLimit: z.string(),
})

export type Config = z.infer<typeof configSchema>

const fetchOne = (sendRequester: HTTPSendRequester, url: string): LedgerHead => {
	const response = sendRequester.sendRequest({ method: 'GET', url }).result()
	if (response.statusCode !== 200) {
		throw new Error(`ledger head request to ${url} failed with status ${response.statusCode}`)
	}
	return parseHead(Buffer.from(response.body).toString('utf-8'))
}

/**
 * Every node fetches the head from TWO independent publications and requires them to agree; consensus then
 * requires all nodes to have seen the same result. If either source is down or they differ, nothing is anchored.
 */
const fetchHead = (sendRequester: HTTPSendRequester, config: Config): LedgerHead =>
	agreeOnHead(fetchOne(sendRequester, config.headUrl), fetchOne(sendRequester, config.headUrlMirror))

function evmClientFor(config: Config) {
	const network = getNetwork({ chainFamily: 'evm', chainSelectorName: config.chainSelectorName, isTestnet: true })
	if (!network) throw new Error(`network not found for chain selector name: ${config.chainSelectorName}`)
	return new cre.capabilities.EVMClient(network.chainSelector.selector)
}

/** Reads the Data Feed price and writes (ledger head, price) to LedgerAnchor through a CRE report. */
export function anchorLedger(runtime: Runtime<Config>, head: LedgerHead): string {
	const config = runtime.config
	const evmClient = evmClientFor(config)

	const feed = new AggregatorV3(evmClient, config.priceFeedAddress as Address)
	const pair = feed.description(runtime)
	const decimals = feed.decimals(runtime)
	const [, answer, , updatedAt] = feed.latestRoundData(runtime)
	runtime.log(`Data Feed ${pair} ${config.priceFeedAddress}: ${formatPrice(answer, decimals)} (updatedAt ${updatedAt})`)

	const report = encodeAnchorReport(head, { answer, decimals, updatedAt })
	const anchor = new LedgerAnchor(evmClient, config.anchorAddress as Address)
	const response = anchor.writeReport(runtime, report, { gasLimit: config.gasLimit })
	if (response.txStatus !== TxStatus.SUCCESS) {
		throw new Error(`failed to write report: ${response.errorMessage || response.txStatus}`)
	}
	const txHash = response.txHash ? bytesToHex(response.txHash) : '0x'
	runtime.log(`Anchored seq ${head.seq} head ${head.hash} at tx ${txHash}`)
	return JSON.stringify({ seq: head.seq, head: head.hash, symbol: head.symbol, feed: pair, price: formatPrice(answer, decimals), txHash })
}

export const onCronTrigger = (runtime: Runtime<Config>, payload: CronPayload): string => {
	if (!payload.scheduledExecutionTime) throw new Error('scheduled execution time is required')
	runtime.log(`Anchoring ledger head from ${runtime.config.headUrl} and ${runtime.config.headUrlMirror}`)
	const head = new cre.capabilities.HTTPClient()
		.sendRequest(runtime, fetchHead, consensusIdenticalAggregation<LedgerHead>())(runtime.config)
		.result()
	return anchorLedger(runtime, head)
}

export function initWorkflow(config: Config) {
	return [cre.handler(new cre.capabilities.CronCapability().trigger({ schedule: config.schedule }), onCronTrigger)]
}
