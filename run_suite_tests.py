import asyncio, os, socket, websockets
from block1_dispatcher import sub_wasm_listener, ss58_to_h160
from block2_aimd import AsyncTokenBucketAIMD
import block3_killswitch as b3
from block4_exporter import ForensicExporterDora

async def run_test_1():
    print("[TEST 1] Initializing Mock Substrate-WASM WebSocket OOM & Recovery...")
    async def mock_handler(ws):
        await ws.recv()
        await ws.send("A" * (2**21)) # Exceeds max_size -> trigger Frame OOM / ConnectionClosed

    server = await websockets.serve(mock_handler, "127.0.0.1", 9944)
    q = asyncio.Queue()
    state = {"is_reconnected": False}
    
    listener_task = asyncio.create_task(sub_wasm_listener("ws://127.0.0.1:9944", q, state))
    await asyncio.sleep(0.3)
    server.close()
    await server.wait_closed()
    await listener_task
    
    assert state["is_reconnected"] is True, "Test 1 Failed: is_reconnected flag was not set"
    h160 = ss58_to_h160("5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY")
    assert len(h160) == 42 and h160.startswith("0x"), f"Test 1 Failed: H160 len={len(h160)}"
    print(f" -> [PASS] Test 1: state['is_reconnected']={state['is_reconnected']}, H160={h160}")

async def run_test_2():
    print("[TEST 2] Verifying Adaptive AIMD Token Bucket 429 Throttle & 5-Step Warm-up...")
    bucket = AsyncTokenBucketAIMD(initial_rate=10)
    bucket.record_rtt(4000.0) # Injected 4000ms delay spike
    bucket.record_rtt(4200.0)
    mad_val = bucket.calculate_mad()
    bucket.handle_rate_limit() # Captured 429
    assert bucket.semaphore._value == 1, f"Expected semaphore value 1, got {bucket.semaphore._value}"
    assert len(bucket.rtt_history) == 5, f"Expected 5 warm-up entries, got {len(bucket.rtt_history)}"
    print(f" -> [PASS] Test 2: Rate compressed. semaphore._value={bucket.semaphore._value}, rtt_history={bucket.rtt_history}, MAD={mad_val}")

async def run_test_3():
    print("[TEST 3] Testing L4 Socket Kill Switch Gate & Zero-Packet Leakage...")
    b3.install_kill_switch()
    b3.SYS_GATEWAY_STATUS["vpn_active"] = False
    captured_ex = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("1.1.1.1", 80))
    except b3.NetworkLayerException:
        captured_ex = True
    finally:
        b3.uninstall_kill_switch()
        b3.SYS_GATEWAY_STATUS["vpn_active"] = True

    assert captured_ex is True, "Test 3 Failed: NetworkLayerException was not raised!"
    assert b3.raw_packet_sent_bytes == 0, f"Test 3 Failed: Leaked packets={b3.raw_packet_sent_bytes}"
    print(f" -> [PASS] Test 3: NetworkLayerException intercepted. raw_packet_sent_bytes={b3.raw_packet_sent_bytes}")

async def run_test_4():
    print("[TEST 4] Validating Stochastic Dora Forensic Exporter Deduplication Hash Collision...")
    sub_sample = ["blk #1029381 hash=0x9182", "transfer 500 DOT to 5GrwvaEF"]
    evm_sample = ["0x889102 txLog Topic=0xddf252ad", "Approval(owner, spender, 1000)"]
    
    hash_1 = ForensicExporterDora.compile_report(sub_sample, evm_sample, "report.md")
    assert os.path.exists("report.md")
    
    hash_2 = ForensicExporterDora.compile_report(sub_sample, evm_sample, "report.md")
    assert hash_1 != hash_2, f"Test 4 Failed: Hash collision detected: {hash_1} == {hash_2}"
    print(f" -> [PASS] Test 4: report.md created. hash_1={hash_1[:16]}... != hash_2={hash_2[:16]}...")

async def main():
    print("=" * 65)
    print("PORTALDOT V3 - UNIFIED RUNTIME TEST SUITE (MORNIX-GRADE 2026)")
    print("=" * 65)
    await run_test_1()
    await run_test_2()
    await run_test_3()
    await run_test_4()
    print("=" * 65)
    print("ALL 4 INTEGRATION SUITE TESTS COMPLETED: 100% SUCCESSFUL")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
