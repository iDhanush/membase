# membase

python sdk for membase operation: memory, knowledge, chain, auth etc.

## Usage

### install

```shell
pip install git+https://github.com/unibaseio/membase.git
# or clone into local
git clone https://github.com/unibaseio/membase.git
cd membase
pip install -e .
```

### memory

- single memory instance, support upload to storage hub

```python
from membase.memory.message import Message
from membase.memory.buffered_memory import BufferedMemory

memory = BufferedMemory(membase_account="default",auto_upload_to_hub=True)
msg = Message(
    name = "agent9527",
    content = "Hello! How can I help you?",
    role="assistant",
    metadata="help info"
)
memory.add(msg)
```

### multi-memory

- support conversation switch
- support conversation preload from storage hub

```python
from membase.memory.multi_memory import MultiMemory
from membase.memory.message import Message

mm = MultiMemory(
    membase_account="default",
    auto_upload_to_hub=True,
    preload_from_hub = True, # this will preload all conversation of membase_account
)
msg = Message(
    name = "agent9527",
    content = "Hello! How can I help you?",
    role="assistant",
    metadata="help info"
)

conversation_id='your_conversation'
mm.add(msg, conversation_id)
```

### knowledge

```python
from membase.knowledge.chroma import ChromaKnowledgeBase
from membase.knowledge.document import Document

kb = ChromaKnowledgeBase(
    persist_directory="/tmp/test",
    membase_account="default",
    auto_upload_to_hub=True)
doc = Document(
    content="The quick brown fox jumps over the lazy dog.",
    metadata={"source": "test", "date": "2025-03-05"}
)
kb.add_documents(doc)
```

### chain task

- env

```shell
export MEMBASE_ID="<any unique string>"
export MEMBASE_ACCOUNT="<account name, 0x...>"
export MEMBASE_SECRET_KEY="<secret key>"
```

```python
from membase.chain.chain import membase_chain

# register task with id and price<minimal staking>
# as task owner
task_id = "task0227"
price = 100000
membase_chain.createTask(task_id, price)

# another one
# join this task, and staking
agent_id = "alice"
membase_chain.register(agent_id)
membase_chain.joinTask(task_id, agent_id)

# another one
agent_id = "bob"
membase_chain.register(agent_id)
membase_chain.joinTask(task_id, agent_id)

# finish task
# 95% belongs to winner: agent_id, 5% belongs to task owner
# call by task owner
membase_chain.finishTask(task_id, agent_id)

# show info
membase_chain.getTask(task_id)
```
