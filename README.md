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

## โครงสร้าง

- `app/main.py` : FastAPI routes
- `app/blockchain.py` : แกน blockchain และ consensus
- `app/schemas.py` : request schemas
- `app/static/*` : UI ที่ backend เสิร์ฟที่ `/ui`
- `index.py` : Vercel entrypoint สำหรับ backend deployment
- `frontend/*` : static frontend สำหรับ deploy แยกบน Vercel
- `render.yaml` : ตัวอย่าง config สำหรับ Render
- `railway.json` : ตัวอย่าง config สำหรับ Railway
- `Procfile` : start command สำหรับ PaaS ที่รองรับ Procfile

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
3. deploy
4. เปิด `https://your-project.vercel.app/ui`

### ทางที่ 2: Deploy UI บน Vercel และ deploy backend บน Render หรือ Railway

เหมาะกับการใช้งานจริงกว่า เพราะ backend จะรันเป็น service ต่อเนื่อง

backend:

- ใช้ root repo นี้บน Render หรือ Railway
- start command คือ `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- มีไฟล์ `render.yaml`, `railway.json`, `Procfile` ให้แล้ว

frontend:

- ใช้โฟลเดอร์ `frontend/` เป็น project root บน Vercel
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
