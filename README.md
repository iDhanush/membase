
# 🧠 Membase: Decentralized Memory & Knowledge Layer for AI Agents

**Membase** is the decentralized, high-performance memory infrastructure powering Unibase.  
It enables AI agents to securely store, retrieve, and manage long-term memory, knowledge, and on-chain collaboration — with native support for persistence, indexing, and multi-agent coordination.

---

## 🚀 Key Features

- **Multi-Conversational Memory** — Store, switch, preload and upload multi-threaded conversations
- **Knowledge Base Integration** — Add structured documents with metadata for retrieval-augmented generation (RAG)
- **On-Chain Task Management** — Register, assign, and verify AI agent collaboration with token incentives
- **Storage Hub Sync** — Real-time integration with the Membase storage hub (`https://testnet.hub.membase.io/`)
- **Web3-Native Auth** — Full support for chain-based identity and access control

---

## 📦 Installation

```bash
# Option 1: Install directly
pip install git+https://github.com/unibaseio/membase.git

# Option 2: Clone and install locally
git clone https://github.com/unibaseio/membase.git
cd membase
pip install -e .
```

---

## 🧩 Usage Examples

### 🔹 Multi-Conversation Memory

```python
from membase.memory.multi_memory import MultiMemory
from membase.memory.message import Message

mm = MultiMemory(
    membase_account="default",
    auto_upload_to_hub=True,
    preload_from_hub=True,
)

msg = Message(
    name="agent9527",
    content="Hello! How can I help you?",
    role="assistant",
    metadata="greeting"
)

mm.add(msg, conversation_id="chat_session_001")
```

### 🔹 Buffered Memory (Single Session)

```python
from membase.memory.message import Message
from membase.memory.buffered_memory import BufferedMemory

memory = BufferedMemory(
    membase_account="default",
    auto_upload_to_hub=True
)

msg = Message(
    name="agent9527",
    content="Welcome to Unibase!",
    role="assistant",
    metadata="intro"
)

memory.add(msg)
```

---

### 📚 Knowledge Base

```python
from membase.knowledge.chroma import ChromaKnowledgeBase
from membase.knowledge.document import Document

kb = ChromaKnowledgeBase(
    persist_directory="/tmp/test_kb",
    membase_account="default",
    auto_upload_to_hub=True
)

doc = Document(
    content="The quick brown fox jumps over the lazy dog.",
    metadata={"source": "example", "date": "2025-03-05"}
)

kb.add_documents(doc)
```

---

## 🔗 On-Chain Task Collaboration

### ✅ Set Environment Variables

```bash
export MEMBASE_ID="my_agent_id"
export MEMBASE_ACCOUNT="0xYourBNBChainAccount"
export MEMBASE_SECRET_KEY="your_private_key"
```

### 🛠 Register and Complete a Task

```python
from membase.chain.chain import membase_chain

membase_chain.createTask("task0227", price=100000)

membase_chain.register("alice")
membase_chain.joinTask("task0227", "alice")

membase_chain.register("bob")
membase_chain.joinTask("task0227", "bob")

membase_chain.finishTask("task0227", "alice")

membase_chain.getTask("task0227")
```

---

## 📂 Hub Storage

- [https://testnet.hub.membase.io/](https://testnet.hub.membase.io/)
- Automatically syncs memory and knowledge for all agents
- Powers persistent and decentralized multi-agent memory

---

## 🛡 Security & Notes

- Agent IDs and accounts are cryptographically verified
- All updates are signed and traceable via blockchain
- Requires testnet BNB for certain operations

---

## 📄 License

MIT License © Unibase 2024  
Issues & Contributions: <https://github.com/unibaseio/membase/issues>
