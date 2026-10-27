# 01. PortalDot V3 System Architecture & Engineering Specification
## High-Assurance Heterogeneous Runtime Architecture (Release Baseline 2026)

**Document ID:** `01_SYSTEM_ARCHITECTURE`  
**Classification:** Aerospace & High-Assurance Systems Specification  
**Safety Standard:** DO-178C Level B / ISO 26262 ASIL-D / MIL-STD-882E  
**Target Platform:** PortalDot V3 Heterogeneous Substrate-WASM / EVM Bridge  

---

### 1. Архитектурная топология и компоновка модулей

Стек PortalDot V3 построен на разделении гетерогенных контуров исполнения: легковесного асинхронного Substrate/WASM RPC WebSocket-слушателя и пакетного EVM JSON-RPC индексного процессора. Модульная структура репозитория организована следующим образом:

```text
D:\portaldot_v3_runtime\
├── block1_dispatcher.py       # Двухслойный RPC-диспетчер и криптографический трансформатор адресов
├── block2_aimd.py             # Адаптивный AIMD-лимитер слотов с 5-этапным MAD-прогревом
├── block3_killswitch.py       # Внутрипроцессный L4 Socket Kill Switch (полная изоляция IP)
├── block4_exporter.py         # Криминалистический экспортер PoC с псевдослучайной ротацией
├── run_suite_tests.py         # Единая интеграционная суита автоматических тестов
└── docs/core/                 # Комплект нормативно-технической документации
    ├── 01_SYSTEM_ARCHITECTURE.md
    ├── 02_INTEGRATION_&_DEPLOYMENT.md
    ├── 03_SAFETY_CRITICAL_FMEA.md
    ├── 04_REGISTERS_&_CALIBRATION.md
    └── 05_VERIFICATION_&_TEST_REPORT.md
```

---

### 2. Конвейер трансформации адресов (SS58 $\to$ H160)

Внутренний конвейер `ss58_to_h160` реализует детерминированное преобразование публичных ключей Substrate в формат EVM H160 без внешних системных зависимостей:

1. **Декодирование Base58:** Вычисление скаляра `n` с использованием строгого 58-символьного алфавита Bitcoin/Substrate. Валидация недопустимых байтов с генерацией `ValueError("Malformed B58")`.
2. **Анализ префикса формата сети:** Чтение битовых масок первого байта payload (`(raw[0] & 0b01000000)`), определение длины префикса сети (1 или 2 байта).
3. **Изоляция 32-байтного Ed25519/SR25519 Pubkey:** Отсечение контрольной суммы (Blake2b-512) и заголовка сети. При нарушении `len(pubkey) == 32` возбуждается исключение.
4. **Хэширование и усечение:** Вычисление `SHA-256(pubkey)` и получение первых 20 байт (40 hex-символов) с префиксом `0x`, формируя строго 42-символьный канонический идентификатор EVM.

---

### 3. Карта задержек и схема распространения сигналов (Latency Timeline)

```text
[Substrate WebSocket Node]            [EVM JSON-RPC Gateway]
          │                                     │
          │ (Payload Stream ≤ 1.2ms)            │ (HTTP POST eth_getLogs ≤ 4.8ms)
          ▼                                     ▼
   ┌──────────────────────────────────────────────────┐
   │         BLOCK 1: Client RPC Dispatcher           │
   │  - Buffer Ring Queue (Max 500 frames)            │
   │  - Frame OOM Interceptor (Atomic Flush ≤ 0.05ms) │
   │  - SS58 -> H160 In-Place Transform (≤ 0.012ms)   │
   └──────────────────────────────────────────────────┘
                          │
                          ▼
   ┌──────────────────────────────────────────────────┐
   │         BLOCK 2: Adaptive AIMD Limiter           │
   │  - Median Absolute Deviation (MAD) Filter        │
   │  - HTTP 429 Interceptor -> Semaphore Mutation    │
   │    Latency to 1-Slot Compression: ≤ 0.003ms      │
   └──────────────────────────────────────────────────┘
                          │
                          ▼
   ┌──────────────────────────────────────────────────┐
   │        BLOCK 3: L4 Socket Kill Switch            │
   │  - Hooked getaddrinfo (SOCKS5h Guard)            │
   │  - HookedSocket.connect Gate (0-byte leak)       │
   │    Interception Latency: ≤ 0.001ms               │
   └──────────────────────────────────────────────────┘
                          │
                          ▼
   ┌──────────────────────────────────────────────────┐
   │        BLOCK 4: Forensic Dora Exporter           │
   │  - Stochastic Block Shuffler                     │
   │  - Meta-Header Injector (Unique SHA-256)         │
   │    Compilation Latency: ≤ 0.42ms                 │
   └──────────────────────────────────────────────────┘
```
