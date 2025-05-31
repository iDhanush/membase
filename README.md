# Membase: Decentralized Memory Layer for AI Agents

**Membase** is a high-performance decentralized AI memory layer designed for persistent conversation storage, scalable knowledge bases, and secure on-chain collaboration tasks — built for the next generation of intelligent agents.

---

## ✨ Features

- **On-Chain Identity Management**  
  Secure cryptographic identity verification and agent registration on blockchain, enabling trustless collaboration, verifiable interactions, and autonomous task coordination in decentralized multi-agent ecosystems.

- **Multi-Memory Management**  
  Manage multiple conversation threads with preload and auto-upload support to Membase Hub.

- **Buffered Single Memory**  
  Store and sync a conversation history with decentralized storage hubs.

- **Knowledge Base Integration**  
  Build, expand, and synchronize agent knowledge using Chroma-based vector storage.

- **Chain Task Coordination**  
  Create, join, and settle on-chain collaborative tasks with decentralized rewards.

- **Secure and Scalable**  
  Designed for millions of conversations and knowledge objects, with blockchain-based verification.

---

# 🚀 Quick Start

## Installation

```bash
pip install git+https://github.com/unibaseio/membase.git
# or clone locally
git clone https://github.com/unibaseio/membase.git
cd membase
pip install -e .
```

---

# ⛓️ Identity Register

- Environment Variables

```bash
export MEMBASE_ID="<any unique string>"
export MEMBASE_ACCOUNT="<account address>"
export MEMBASE_SECRET_KEY="<account secret>"
```

- Registeration and Verification

```python
from membase.chain.chain import membase_chain

# register onchain
agent_name = "your_agent_name"
membase_chain.register(agent_name)

# buy auth, then new agent can visit agent_name's resource
new_agent = "another_agent_name"
membase_chain.buy(agent_name, new_agent)

# check persmission
# get address and valid sign with new_agent_address
new_agent_address = membase_chain.get_agent(new_agent)
valid_sign(sign, new_agent_address)
# check onchain persmission
if membase_chain.has_auth(agent_name, new_agent):
  print("has permission")
```

# 🧠 Multi-Memory Example

Manage multiple conversation threads simultaneously.

```python
from membase.memory.multi_memory import MultiMemory
from membase.memory.message import Message

mm = MultiMemory(
    membase_account="default",
    auto_upload_to_hub=True,
    preload_from_hub=True
)

msg = Message(
    name="agent9527",
    content="Hello! How can I help you?",
    role="assistant",
    metadata="help info"
)

conversation_id = 'your_conversation'
mm.add(msg, conversation_id)
```

🌐 Hub Access: Visit your conversations at [https://testnet.explorer.unibase.com/](https://testnet.explorer.unibase.com/)

---

# 🗂️ Single Memory Example

Manage a single conversation buffer.

```python
from membase.memory.message import Message
from membase.memory.buffered_memory import BufferedMemory

memory = BufferedMemory(membase_account="default", auto_upload_to_hub=True)
msg = Message(
    name="agent9527",
    content="Hello! How can I help you?",
    role="assistant",
    metadata="help info"
)
memory.add(msg)
```

---

# 📚 Knowledge Base Example

Store and manage knowledge documents using Chroma integration.

```python
from membase.knowledge.chroma import ChromaKnowledgeBase
from membase.knowledge.document import Document

kb = ChromaKnowledgeBase(
    persist_directory="/tmp/test",
    membase_account="default",
    auto_upload_to_hub=True
)

doc = Document(
    content="The quick brown fox jumps over the lazy dog.",
    metadata={"source": "test", "date": "2025-03-05"}
)

kb.add_documents(doc)
```

---

# 🔗 Chain Task Example

Coordinate collaborative tasks with staking and settlement on-chain.

## Environment Variables

```bash
export MEMBASE_ID="<any unique string>"
export MEMBASE_ACCOUNT="<account address>"
export MEMBASE_SECRET_KEY="<account secret>"
```

## Code Example

```python
from membase.chain.chain import membase_chain

task_id = "task0227"
price = 100000

# Create a new collaborative task
membase_chain.createTask(task_id, price)

# Agent "alice" joins and stakes
agent_id = "alice"
membase_chain.register(agent_id)
membase_chain.joinTask(task_id, agent_id)

# Agent "bob" joins and stakes
agent_id = "bob"
membase_chain.register(agent_id)
membase_chain.joinTask(task_id, agent_id)

# Task owner finishes and distributes rewards
membase_chain.finishTask(task_id, agent_id="alice")

# Query task info
membase_chain.getTask(task_id)
```

---

# 📜 License

MIT License. See [LICENSE](./LICENSE) for details.

---

# 📞 Contact

- Website: [https://www.unibase.com](https://www.unibase.com)
- GitHub Issues: [Membase Issues](https://github.com/unibaseio/membase/issues)
- Email: <support@unibase.com>
