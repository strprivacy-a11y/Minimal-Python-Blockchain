from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.blockchain import Blockchain
from app.schemas import MessageResponse, NodeList, TransactionCreate
from app.storage import create_state_store


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
node_id = uuid4().hex
state_store = create_state_store()
blockchain = Blockchain(node_id=node_id, state_store=state_store)

app = FastAPI(
    title="Blockchain Simulator API",
    version="1.0.0",
    description="Simple multi-node blockchain simulation with transaction and mining endpoints.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_model=MessageResponse)
def root() -> dict[str, str]:
    return {
        "message": "Blockchain simulator is running.",
        "node_id": node_id,
        "storage_backend": state_store.backend_name,
    }


@app.get("/ui", include_in_schema=False)
def ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/status")
def get_status() -> dict[str, object]:
    return {
        "message": "Blockchain simulator is running.",
        "node_id": node_id,
        "difficulty_prefix": blockchain.difficulty_prefix,
        "chain_length": len(blockchain.chain),
        "pending_transactions": len(blockchain.current_transactions),
        "nodes": sorted(blockchain.nodes),
        "storage_backend": state_store.backend_name,
    }


@app.get("/chain")
def get_chain() -> dict[str, object]:
    return {
        "chain": blockchain.chain,
        "length": len(blockchain.chain),
    }


@app.get("/transactions")
def get_pending_transactions() -> dict[str, object]:
    return {
        "pending_transactions": blockchain.current_transactions,
        "count": len(blockchain.current_transactions),
    }


@app.post("/transactions", response_model=MessageResponse, status_code=201)
def create_transaction(payload: TransactionCreate) -> dict[str, object]:
    next_block_index = blockchain.create_transaction(
        sender=payload.sender,
        recipient=payload.recipient,
        amount=payload.amount,
    )
    return {
        "message": f"Transaction will be added to block {next_block_index}",
        "next_block_index": next_block_index,
    }


@app.post("/mine")
def mine_block() -> dict[str, object]:
    if not blockchain.current_transactions:
        raise HTTPException(status_code=400, detail="No pending transactions to mine.")

    previous_block = blockchain.last_block
    proof = blockchain.proof_of_work(previous_block["proof"])

    blockchain.create_transaction(
        sender="0",
        recipient=blockchain.node_id,
        amount=1,
    )
    block = blockchain.create_block(proof=proof, previous_hash=blockchain.hash(previous_block))

    return {
        "message": "New block mined successfully",
        "block": block,
    }


@app.post("/nodes/register")
def register_nodes(payload: NodeList) -> dict[str, object]:
    registered_nodes: list[str] = []
    for node in payload.nodes:
        try:
            registered_nodes.append(blockchain.register_node(node))
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "message": "Nodes registered successfully",
        "total_nodes": sorted(blockchain.nodes),
        "registered_nodes": registered_nodes,
    }


@app.get("/nodes")
def list_nodes() -> dict[str, object]:
    return {
        "nodes": sorted(blockchain.nodes),
        "count": len(blockchain.nodes),
    }


@app.post("/nodes/resolve")
def resolve_nodes() -> dict[str, object]:
    try:
        replaced = blockchain.resolve_conflicts()
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Consensus failed: {error}") from error

    if replaced:
        return {
            "message": "Local chain was replaced",
            "chain": blockchain.chain,
            "length": len(blockchain.chain),
        }

    return {
        "message": "Local chain is authoritative",
        "chain": blockchain.chain,
        "length": len(blockchain.chain),
    }
