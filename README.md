# Blockchain Simulator API

โปรเจกต์นี้เป็นตัวอย่างระบบจำลอง Blockchain แบบหลายโหนดด้วย Python และ FastAPI โดยสามารถ:

- สร้างธุรกรรมผ่าน HTTP API
- ขุด block ผ่าน HTTP API
- ดู chain และรายการธุรกรรมที่รอขุด
- ลงทะเบียนโหนดอื่น
- เรียก consensus แบบง่ายเพื่อ sync chain ที่ยาวกว่า

## โครงสร้าง

- `app/main.py` : FastAPI routes
- `app/blockchain.py` : แกน blockchain และ consensus
- `app/schemas.py` : request schemas

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
