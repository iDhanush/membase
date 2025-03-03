# membase

python sdk for membase operation

## Usage

- MEMBASE_ACCOUNT is set

### install

```shell
pip install git+https://github.com/unibaseio/membase.git
# or clone into local
git clone https://github.com/unibaseio/membase.git
cd membase
pip insrall -e .
```

### memory

```python
from membase.memory.message import Message
from membase.memory.buffered_memory import BufferedMemory

memory = BufferedMemory(persistence_in_remote=True)
msg = Message(
            "agent",
            "Hello! How can I help you?",
            role="assistant",
            metadata="md"
        )
memory.add(msg)
```
