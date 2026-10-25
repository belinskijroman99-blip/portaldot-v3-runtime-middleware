import asyncio, statistics

class AsyncTokenBucketAIMD:
    def __init__(self, initial_rate=10):
        self._rate = initial_rate
        self.semaphore = asyncio.Semaphore(initial_rate)
        self.rtt_history = [30.0] * 5

    def warm_up(self):
        self.rtt_history.clear()
        self.rtt_history.extend([30.0] * 5)

    def calculate_mad(self):
        if len(self.rtt_history) < 2: return 0.0
        med = statistics.median(self.rtt_history)
        return statistics.median([abs(x - med) for x in self.rtt_history])

    def record_rtt(self, rtt_ms):
        self.rtt_history.append(float(rtt_ms))
        if len(self.rtt_history) > 50: self.rtt_history.pop(0)

    def handle_rate_limit(self):
        self._rate = max(1, int(self._rate // 10))
        self.semaphore._value = max(1, int(self._rate // 10))
        self.warm_up()

    async def acquire(self):
        await self.semaphore.acquire()

    def release(self):
        self.semaphore.release()
