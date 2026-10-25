import asyncio, json, websockets, aiohttp, hashlib

async def sub_wasm_listener(uri, queue, state_flag, max_q=500):
    payload = json.dumps({"id": 1, "jsonrpc": "2.0", "method": "chain_subscribeNewHeads", "params": []})
    while True:
        try:
            async with websockets.connect(uri, ping_interval=10, ping_timeout=5, close_timeout=1, max_size=2**20) as ws:
                await ws.send(payload)
                async for raw in ws:
                    if queue.qsize() >= max_q:
                        try: queue.get_nowait()
                        except asyncio.QueueEmpty: pass
                    await queue.put(json.loads(raw))
                    await asyncio.sleep(0)
        except Exception:
            state_flag["is_reconnected"] = True
            while not queue.empty():
                try: queue.get_nowait()
                except asyncio.QueueEmpty: break
            await asyncio.sleep(0.05)
            break

async def evm_index_logs(session, rpc_url, address, topics, from_blk, to_blk):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{"address": address, "topics": topics, "fromBlock": hex(from_blk), "toBlock": hex(to_blk)}]}
    async with session.post(rpc_url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
        res = (await resp.json()).get("result", [])
        return [{"tx": log["transactionHash"], "log_idx": int(log["logIndex"], 16), "topics": [t[2:] for t in log.get("topics", []) if len(t) == 66], "data": bytes.fromhex(log.get("data", "0x")[2:])} for log in res if "topics" in log]

def ss58_to_h160(ss58_addr: str) -> str:
    n = 0
    for char in ss58_addr:
        idx = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(char)
        if idx == -1: raise ValueError("Malformed B58")
        n = n * 58 + idx
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pubkey = raw[(1 if (raw[0] & 0b01000000) == 0 else 2):-2]
    if len(pubkey) != 32: raise ValueError("Invalid pubkey length")
    return "0x" + hashlib.sha256(pubkey).hexdigest()[:40]
