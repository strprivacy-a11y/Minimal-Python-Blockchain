const statusFields = {
  activeBaseUrl: document.querySelector("#active-base-url"),
  nodeId: document.querySelector("#node-id"),
  difficulty: document.querySelector("#difficulty"),
  chainLength: document.querySelector("#chain-length"),
  pendingCount: document.querySelector("#pending-count"),
  latestBlock: document.querySelector("#latest-block"),
  peerCount: document.querySelector("#peer-count"),
};

const transactionForm = document.querySelector("#transaction-form");
const nodesForm = document.querySelector("#nodes-form");
const quickNodeForm = document.querySelector("#quick-node-form");
const mineButton = document.querySelector("#mine-button");
const resolveButton = document.querySelector("#resolve-button");
const nodeSelect = document.querySelector("#node-select");
const useCurrentNodeButton = document.querySelector("#use-current-node");
const logPanel = document.querySelector("#response-log");
const transactionsList = document.querySelector("#transactions-list");
const nodesList = document.querySelector("#nodes-list");
const chainList = document.querySelector("#chain-list");
const chainVisual = document.querySelector("#chain-visual");
const ACTIVE_BASE_URL_STORAGE_KEY = "blockchain-active-base-url";
const NODE_TARGETS_STORAGE_KEY = "blockchain-known-targets";

function getBootstrapConfig() {
  return window.BLOCKCHAIN_CONFIG || {};
}

function getQueryApiTarget() {
  return new URLSearchParams(window.location.search).get("api");
}

function normalizeBaseUrl(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed) {
    return "";
  }

  const candidate = /^https?:\/\//.test(trimmed) ? trimmed : `http://${trimmed}`;
  try {
    const url = new URL(candidate);
    return url.origin;
  } catch {
    return "";
  }
}

function loadStoredTargets() {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(NODE_TARGETS_STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function persistKnownTargets() {
  window.localStorage.setItem(NODE_TARGETS_STORAGE_KEY, JSON.stringify(knownTargets));
}

function persistActiveBaseUrl() {
  window.localStorage.setItem(ACTIVE_BASE_URL_STORAGE_KEY, activeBaseUrl);
}

function buildInitialTargets() {
  const config = getBootstrapConfig();
  const configTargets = Array.isArray(config.apiTargets) ? config.apiTargets : [];
  const localTargets = ["http://127.0.0.1:8001", "http://127.0.0.1:8002", "http://127.0.0.1:8003"];
  const rawTargets = [
    config.defaultApiBaseUrl,
    window.location.origin,
    getQueryApiTarget(),
    ...configTargets,
    ...loadStoredTargets(),
    ...localTargets,
  ];

  return Array.from(new Set(rawTargets.map(normalizeBaseUrl).filter(Boolean)));
}

function buildInitialActiveBaseUrl() {
  const config = getBootstrapConfig();
  const candidates = [
    getQueryApiTarget(),
    window.localStorage.getItem(ACTIVE_BASE_URL_STORAGE_KEY),
    config.defaultApiBaseUrl,
    window.location.origin,
  ];

  for (const candidate of candidates) {
    const normalized = normalizeBaseUrl(candidate);
    if (normalized) {
      return normalized;
    }
  }

  return window.location.origin;
}

let knownTargets = buildInitialTargets();
let activeBaseUrl = buildInitialActiveBaseUrl();

function updateNodeSelector() {
  if (!knownTargets.includes(activeBaseUrl)) {
    knownTargets.unshift(activeBaseUrl);
  }
  nodeSelect.innerHTML = knownTargets
    .map((target) => `<option value="${target}">${target}</option>`)
    .join("");
  nodeSelect.value = activeBaseUrl;
  statusFields.activeBaseUrl.textContent = activeBaseUrl;
  persistKnownTargets();
  persistActiveBaseUrl();
}

function addKnownTarget(value) {
  const normalized = normalizeBaseUrl(value);
  if (!normalized) {
    throw new Error("Invalid node URL. Use format like http://127.0.0.1:8002");
  }
  if (!knownTargets.includes(normalized)) {
    knownTargets.push(normalized);
  }
  activeBaseUrl = normalized;
  updateNodeSelector();
}

function writeLog(title, payload) {
  const stamp = new Date().toLocaleTimeString();
  const message = `[${stamp}] ${title}\n${JSON.stringify(payload, null, 2)}\n\n`;
  logPanel.textContent = message + logPanel.textContent;
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${activeBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    throw new Error(data.detail || data.message || `Request failed: ${response.status}`);
  }

  return data;
}

function renderEmpty(target, message) {
  target.innerHTML = `<div class="list-item muted">${message}</div>`;
}

function renderTransactions(items) {
  if (!items.length) {
    renderEmpty(transactionsList, "No pending transactions.");
    return;
  }

  transactionsList.innerHTML = items
    .map(
      (tx, index) => `
        <div class="list-item">
          <strong>TX #${index + 1}</strong>
          <div><span class="muted">From:</span> <span class="mono">${tx.sender}</span></div>
          <div><span class="muted">To:</span> <span class="mono">${tx.recipient}</span></div>
          <div><span class="muted">Amount:</span> ${tx.amount}</div>
        </div>
      `
    )
    .join("");
}

function renderNodes(items) {
  if (!items.length) {
    renderEmpty(nodesList, "No peer nodes registered.");
    return;
  }

  nodesList.innerHTML = items
    .map(
      (node, index) => `
        <div class="list-item">
          <strong>Peer #${index + 1}</strong>
          <div class="mono">${node}</div>
        </div>
      `
    )
    .join("");
}

function renderChain(chain) {
  if (!chain.length) {
    renderEmpty(chainVisual, "Chain diagram is empty.");
    renderEmpty(chainList, "Chain is empty.");
    return;
  }

  chainVisual.innerHTML = chain
    .map(
      (block, index) => `
        <article class="chain-node">
          <div class="chain-node-head">
            <strong>Block #${block.index}</strong>
            <span class="hash-strip">${index === 0 ? "genesis" : `prev ${String(block.previous_hash).slice(0, 10)}...`}</span>
          </div>
          <div><span class="muted">Proof:</span> ${block.proof}</div>
          <div><span class="muted">TX Count:</span> ${block.transactions.length}</div>
          <div><span class="muted">Time:</span> ${new Date(block.timestamp * 1000).toLocaleTimeString()}</div>
        </article>
      `
    )
    .join("");

  chainList.innerHTML = chain
    .map(
      (block) => `
        <article class="chain-item">
          <strong>Block #${block.index}</strong>
          <div><span class="muted">Timestamp:</span> ${new Date(block.timestamp * 1000).toLocaleString()}</div>
          <div><span class="muted">Proof:</span> ${block.proof}</div>
          <div><span class="muted">Previous Hash:</span> <span class="mono">${block.previous_hash}</span></div>
          <div><span class="muted">Transactions:</span> ${block.transactions.length}</div>
          <pre class="response-log">${JSON.stringify(block.transactions, null, 2)}</pre>
        </article>
      `
    )
    .join("");
}

async function refreshStatus() {
  const status = await apiFetch("/status");
  statusFields.activeBaseUrl.textContent = activeBaseUrl;
  statusFields.nodeId.textContent = status.node_id;
  statusFields.difficulty.textContent = status.difficulty_prefix;
  statusFields.chainLength.textContent = status.chain_length;
  statusFields.pendingCount.textContent = status.pending_transactions;
  statusFields.peerCount.textContent = status.nodes.length;
}

async function refreshTransactions() {
  const data = await apiFetch("/transactions");
  renderTransactions(data.pending_transactions);
}

async function refreshNodes() {
  const data = await apiFetch("/nodes");
  renderNodes(data.nodes);
}

async function refreshChain() {
  const data = await apiFetch("/chain");
  renderChain(data.chain);
  statusFields.latestBlock.textContent = data.length ? `#${data.chain[data.chain.length - 1].index}` : "-";
}

async function refreshAll() {
  await Promise.all([refreshStatus(), refreshTransactions(), refreshNodes(), refreshChain()]);
}

async function handleAction(actionName, callback, button) {
  if (button) {
    button.disabled = true;
  }

  try {
    const result = await callback();
    writeLog(actionName, result);
    await refreshAll();
  } catch (error) {
    writeLog(`${actionName} failed`, { error: error.message });
    window.alert(error.message);
  } finally {
    if (button) {
      button.disabled = false;
    }
  }
}

transactionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(transactionForm);
  const payload = {
    sender: String(formData.get("sender")).trim(),
    recipient: String(formData.get("recipient")).trim(),
    amount: Number(formData.get("amount")),
  };

  await handleAction(
    "Transaction created",
    () =>
      apiFetch("/transactions", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    transactionForm.querySelector("button[type='submit']")
  );

  transactionForm.reset();
});

nodesForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(nodesForm);
  const nodes = String(formData.get("nodes"))
    .split("\n")
    .map((value) => value.trim())
    .filter(Boolean);

  await handleAction(
    "Nodes registered",
    () =>
      apiFetch("/nodes/register", {
        method: "POST",
        body: JSON.stringify({ nodes }),
      }),
    nodesForm.querySelector("button[type='submit']")
  );
});

quickNodeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.querySelector("#quick-node-input");
  try {
    addKnownTarget(input.value);
    input.value = "";
    writeLog("Active node changed", { active_base_url: activeBaseUrl, known_targets: knownTargets });
    await refreshAll();
  } catch (error) {
    writeLog("Add node target failed", { error: error.message });
    window.alert(error.message);
  }
});

mineButton.addEventListener("click", async () => {
  await handleAction(
    "Mining completed",
    () =>
      apiFetch("/mine", {
        method: "POST",
      }),
    mineButton
  );
});

resolveButton.addEventListener("click", async () => {
  await handleAction(
    "Consensus resolved",
    () =>
      apiFetch("/nodes/resolve", {
        method: "POST",
      }),
    resolveButton
  );
});

document.querySelector("#refresh-all-top").addEventListener("click", refreshAll);
document.querySelector("#refresh-transactions").addEventListener("click", refreshTransactions);
document.querySelector("#refresh-nodes").addEventListener("click", refreshNodes);
document.querySelector("#refresh-chain").addEventListener("click", refreshChain);
nodeSelect.addEventListener("change", async (event) => {
  activeBaseUrl = event.target.value;
  persistActiveBaseUrl();
  writeLog("Active node changed", { active_base_url: activeBaseUrl });
  await refreshAll();
});
useCurrentNodeButton.addEventListener("click", async () => {
  addKnownTarget(window.location.origin);
  writeLog("Active node changed", { active_base_url: activeBaseUrl });
  await refreshAll();
});
document.querySelector("#clear-log").addEventListener("click", () => {
  logPanel.textContent = "Log cleared.";
});

updateNodeSelector();
refreshAll().catch((error) => {
  writeLog("Initial load failed", { error: error.message });
});
