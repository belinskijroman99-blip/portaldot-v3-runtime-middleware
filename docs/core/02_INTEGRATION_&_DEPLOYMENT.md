# 02. Integration, Deployment & Runtime Environment
## Aerospace-Grade Deployment & Verification Runbook (Release Baseline 2026)

**Document ID:** `02_INTEGRATION_&_DEPLOYMENT`  
**Classification:** Operational Deployment Guide  
**Compliance Reference:** DO-178C Section 6.4 / ISO 26262 Part 8  

---

### 1. Системные требования и зависимости

Стек PortalDot V3 функционирует в окружении Python 3.11+ / 3.12+ (Windows x86_64 или Linux x86_64). Модули используют фиксированный набор зависимостей:

```text
websockets >= 14.0
aiohttp >= 3.10.0
hashlib (встроенный модуль CPython)
socket, asyncio, statistics, random, uuid (встроенные модули CPython)
```

Установка необходимых библиотек:
```bash
pip install websockets aiohttp
```

---

### 2. Запуск единого верификационного комплекса

Запуск полного интеграционного сьюта выполняется одной детерминированной командой из корня директории:

```bash
python D:\portaldot_v3_runtime\run_suite_tests.py
```

Ожидаемый статус исполнения: код возврата `0`, 4 из 4 тестов завершены в статусе `[PASS]`.

---

### 3. Инициализация параметров среды

При переходе от тестовой имитации к физическим нодам конфигурация осуществляется передачей параметров в фабричные конструкторы модулей:

- **Substrate Node URI:** `ws://127.0.0.1:9944` или защищенный WSS-эндпоинт валидатора (`wss://rpc.polkadot.io`).
- **EVM JSON-RPC Gateway:** `http://127.0.0.1:8545` или приватный RPC провайдера.
- **Ограничитель кольцевого буфера (`max_q`):** По умолчанию зафиксирован на значении `500` кадров. При переполнении буфера старший кадр мгновенно сбрасывается (`queue.get_nowait()`) с нулевым влиянием на поток подписки.
- **Базовый concurrency rate (`initial_rate`):** Инициализируется значением `10` параллельных слотов.
- **Флаг состояния шлюза (`SYS_GATEWAY_STATUS["vpn_active"]`):** При падении VPN-интерфейса в фоновом демоне переключается в `False`, активируя немедленную отсечку на транспортном уровне L4.
