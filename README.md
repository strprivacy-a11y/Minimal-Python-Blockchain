# Minimal Python Blockchain

โปรเจกต์นี้เป็นระบบจำลอง Blockchain ด้วย Python และ FastAPI พร้อม retro terminal-style UI โดยสามารถ:

- สร้างธุรกรรมผ่าน HTTP API
- ขุด block ผ่าน HTTP API
- ดู chain และรายการธุรกรรมที่รอขุด
- ลงทะเบียนโหนดอื่น
- เรียก consensus แบบง่ายเพื่อ sync chain ที่ยาวกว่า

## ความสามารถหลัก

- สร้างธุรกรรมผ่าน HTTP API
- ขุด block ผ่าน HTTP API
- ดู chain และรายการธุรกรรมที่รอขุด
- ลงทะเบียนโหนดอื่น
- เรียก consensus แบบง่ายเพื่อ sync chain ที่ยาวกว่า
- ใช้งานผ่านหน้า UI ที่รันจาก backend เดียวกัน หรือแยก deploy เป็น static frontend ได้
- รองรับ optional persistence ผ่าน Redis หรือ Postgres

## โครงสร้าง

- `app/main.py` : FastAPI routes
- `app/blockchain.py` : แกน blockchain และ consensus
- `app/storage.py` : persistence backend abstraction สำหรับ memory, Redis, Postgres
- `app/schemas.py` : request schemas
- `app/static/*` : UI ที่ backend เสิร์ฟที่ `/ui`
- `index.py` : Vercel entrypoint สำหรับ backend deployment
- `Dockerfile` : container image สำหรับ FastAPI app
- `compose.yaml` : local stack สำหรับ app, Redis, Postgres
- `.env.example` : ตัวอย่าง environment variables สำหรับ storage backend
- `frontend/*` : static frontend สำหรับ deploy แยกบน Vercel
- `vercel.json` : config สำหรับ deploy repo root เป็น Vercel FastAPI demo
- `frontend/vercel.json` : config สำหรับ deploy `frontend/` เป็น static Vercel site
- `render.yaml` : ตัวอย่าง config สำหรับ Render
- `railway.json` : ตัวอย่าง config สำหรับ Railway
- `Procfile` : start command สำหรับ PaaS ที่รองรับ Procfile
- `.github/workflows/ci.yml` : GitHub Actions สำหรับ syntax/config checks
- `.github/workflows/vercel-backend.yml` : GitHub Actions deploy backend ไป Vercel
- `.github/workflows/vercel-frontend.yml` : GitHub Actions deploy frontend ไป Vercel

## ติดตั้ง

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## รัน 1 โหนด

```bash
uvicorn app.main:app --reload --port 8000
```

เปิดหน้า UI ได้ที่:

```text
http://127.0.0.1:8000/ui
```

## รันด้วย Docker

### app อย่างเดียว

```bash
docker compose up --build
```

### app + Redis persistence

```bash
cp .env.example .env
printf 'REDIS_URL=redis://redis:6379/0\n' >> .env
docker compose --profile redis up --build
```

### app + Postgres persistence

```bash
cp .env.example .env
printf 'DATABASE_URL=postgresql://blockchain:blockchain@postgres:5432/blockchain\n' >> .env
docker compose --profile postgres up --build
```

## Deploy ได้ 2 ทาง

### ทางที่ 1: Deploy ทั้ง backend + UI บน Vercel แบบ single-node demo

เหมาะกับเดโมเร็วที่สุด โดยใช้ repo root นี้ตรงๆ

- Vercel จะใช้ `index.py` เป็น FastAPI entrypoint
- UI จะเปิดจาก `/ui`
- API จะอยู่โดเมนเดียวกันกับ UI
- blockchain state ยังอยู่ใน memory

ข้อจำกัดสำคัญ:

- state ไม่ถาวร อาจ reset ได้เมื่อ function instance เปลี่ยน
- ไม่เหมาะกับ multi-node local process แบบ `8001/8002/8003`
- `start_nodes.sh` และ `stop_nodes.sh` ใช้ไม่ได้บน Vercel

ขั้นตอน:

1. import repo นี้เข้า Vercel
2. ใช้ root directory เป็น `/`
3. Vercel จะอ่าน `vercel.json` ที่ repo root
4. deploy
5. เปิด `https://your-project.vercel.app/ui`

ถ้าต้องการใช้ state ที่ไม่หายง่าย ให้ตั้ง environment variable:

```text
REDIS_URL=redis://...
BLOCKCHAIN_STATE_KEY=minimal-python-blockchain:state
```

หรือใช้ Postgres:

```text
DATABASE_URL=postgresql://...
BLOCKCHAIN_STATE_KEY=minimal-python-blockchain:state
```

### ทางที่ 2: Deploy UI บน Vercel และ deploy backend บน Render หรือ Railway

เหมาะกับการใช้งานจริงกว่า เพราะ backend จะรันเป็น service ต่อเนื่อง

backend:

- ใช้ root repo นี้บน Render หรือ Railway
- start command คือ `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- มีไฟล์ `render.yaml`, `railway.json`, `Procfile` ให้แล้ว
- ถ้าต้องการ persistence ข้าม restart ให้ตั้ง `REDIS_URL` หรือ `DATABASE_URL`

frontend:

- ใช้โฟลเดอร์ `frontend/` เป็น project root บน Vercel
- Vercel จะอ่าน `frontend/vercel.json`
- แก้ `frontend/config.js` ให้ชี้ไป backend URL จริงก่อน deploy
- หลัง deploy หน้า UI จะยิง API ไปยัง backend ที่ตั้งไว้

ตัวอย่าง `frontend/config.js`:

```js
window.BLOCKCHAIN_CONFIG = {
  defaultApiBaseUrl: "https://your-backend.example.com",
  apiTargets: [
    "https://your-backend.example.com"
  ]
};
```

สามารถ override backend ชั่วคราวได้ด้วย query string:

```text
https://your-frontend.vercel.app/?api=https://your-backend.example.com
```

## GitHub Actions Deploy

workflow deploy ของ Vercel ถูกเตรียมไว้ 2 ตัว:

- backend: `.github/workflows/vercel-backend.yml`
- frontend: `.github/workflows/vercel-frontend.yml`

GitHub repository secrets ที่ต้องตั้ง:

```text
VERCEL_TOKEN
VERCEL_BACKEND_ORG_ID
VERCEL_BACKEND_PROJECT_ID
VERCEL_FRONTEND_ORG_ID
VERCEL_FRONTEND_PROJECT_ID
```

พฤติกรรม:

- `pull_request` จะ deploy เป็น preview
- `push` ไป `main` จะ deploy เป็น production

## รันหลายโหนด

เปิดหลาย terminal แล้วรันคนละ port:

```bash
uvicorn app.main:app --reload --port 8000
uvicorn app.main:app --reload --port 8001
uvicorn app.main:app --reload --port 8002
```

หรือใช้สคริปต์:

```bash
./start_nodes.sh
```

และหยุดทั้งหมดด้วย:

```bash
./stop_nodes.sh
```

## ตัวอย่าง API

### 1. สร้างธุรกรรม

```bash
curl -X POST http://127.0.0.1:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "alice",
    "recipient": "bob",
    "amount": 15
  }'
```

### 2. ขุด block

```bash
curl -X POST http://127.0.0.1:8000/mine
```

### 3. ดู chain

```bash
curl http://127.0.0.1:8000/chain
```

### 3.1 ดูสถานะโหนด

```bash
curl http://127.0.0.1:8000/status
```

### 3.2 health check

```bash
curl http://127.0.0.1:8000/healthz
```

### 3.3 readiness check

```bash
curl http://127.0.0.1:8000/readyz
```

### 3.4 backup state

```bash
curl http://127.0.0.1:8000/backup
```

### 3.5 restore state

```bash
curl -X POST http://127.0.0.1:8000/restore \
  -H "Content-Type: application/json" \
  -d '{
    "chain": [
      {
        "index": 1,
        "timestamp": 1,
        "transactions": [],
        "proof": 100,
        "previous_hash": "1"
      }
    ],
    "current_transactions": [],
    "nodes": []
  }'
```

### 4. ลงทะเบียนโหนดอื่น

```bash
curl -X POST http://127.0.0.1:8000/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": ["127.0.0.1:8001", "127.0.0.1:8002"]
  }'
```

### 5. สั่ง sync consensus

```bash
curl -X POST http://127.0.0.1:8000/nodes/resolve
```

## หมายเหตุ

- เป็นระบบจำลองเพื่อการเรียนรู้ ไม่ใช่ blockchain production
- ใช้ proof-of-work แบบง่าย
- ธุรกรรมยังไม่รองรับลายเซ็นดิจิทัลหรือยอดคงเหลือจริง
- ถ้า `python3 -m venv` ใช้ไม่ได้บนเครื่องนี้ สามารถติดตั้งแพ็กเกจแบบ local user แทนได้ด้วย `python3 -m pip install --user --break-system-packages -r requirements.txt`
- ถ้าจะใช้ Vercel แบบแยก frontend/backend ให้ตั้งค่า backend URL ใน `frontend/config.js` ก่อน deploy
- ถ้าจะใช้ Vercel แบบ backend เดียวทั้ง UI และ API ให้เปิดที่ `/ui` ไม่ใช่ `/`
- GitHub Actions จะรันเช็ก syntax ของ Python และ shell script ทุก push/PR
- storage backend จะเลือกตามลำดับนี้: `REDIS_URL` -> `DATABASE_URL` -> memory
- ถ้าตั้ง `REDIS_URL` หรือ `DATABASE_URL` ระบบจะพยายามเก็บ `chain`, `pending transactions`, และ `nodes` ลง storage นั้น
- `/healthz` ใช้เช็กว่า process ขึ้นแล้ว ส่วน `/readyz` ใช้เช็กว่า storage backend พร้อมใช้งานจริง
- `/backup` และ `/restore` ใช้ export/import state ระหว่าง environment หรือใช้กู้คืนข้อมูลแบบ manual
