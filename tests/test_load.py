import unittest
import uuid
from unittest.mock import patch

from membase.memory.multi_memory import MultiMemory
from membase.memory.message import Message

class TestMultiMemoryLoad(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.default_account = 'default-' + str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        self.multi_memory = MultiMemory(
            membase_account=self.default_account,
            auto_upload_to_hub=True,
            default_conversation_id=self.conversation_id
        )
        
    def test_add_and_load_from_hub(self):
        """Test adding messages and loading them from hub"""
        # Create test messages
        test_messages = [
            Message(
                content="Hello, world!",
                role="user",
                name="test_user" + str(uuid.uuid4())
            ),
            Message(
                content="Hello, world1!",
                role="user",
                name="test_user" + str(uuid.uuid4())
            )
        ]
        
        # Add messages to first instance
        for msg in test_messages:
            self.multi_memory.add(memories=msg)
    
        
        # Create new instance and load from hub
        new_mm = MultiMemory(
            membase_account=self.default_account,
            auto_upload_to_hub=True,
            default_conversation_id=str(uuid.uuid4()),
            preload_from_hub=True
        )
        
        # Verify conversations were loaded
        self.assertIn(self.conversation_id, new_mm.get_all_conversations())
        
        # Get and verify messages
        loaded_msgs = new_mm.get(conversation_id=self.conversation_id)
        self.assertEqual(len(loaded_msgs), len(test_messages))
        
        # Verify message contents
        for original, loaded in zip(test_messages, loaded_msgs):
            self.assertEqual(original.content, loaded.content)
            self.assertEqual(original.role, loaded.role)
            self.assertTrue(loaded.name.startswith("test_user"))

if __name__ == '__main__':
    unittest.main()
