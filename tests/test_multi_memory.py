import unittest
from typing import List
import uuid
from unittest.mock import patch, MagicMock

from membase.memory.multi_memory import MultiMemory
from membase.memory.message import Message

@patch('membase.memory.multi_memory.hub_client')
class TestMultiMemory(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.multi_memory = MultiMemory(membase_account="test_account", auto_upload_to_hub=True)
        self.test_message = Message(content="test content", role="user", name="test_user")
        
    def test_init_with_default_conversation_id(self):
        """Test initialization with default conversation id"""
        custom_id = "custom_id"
        memory = MultiMemory(default_conversation_id=custom_id)
        self.assertEqual(memory.default_conversation_id, custom_id)
        
    def test_init_without_default_conversation_id(self):
        """Test initialization without default conversation id"""
        memory = MultiMemory()
        self.assertTrue(isinstance(memory.default_conversation_id, str))
        # Should be a valid UUID
        uuid.UUID(memory.default_conversation_id)
        
    def test_update_conversation_id(self):
        """Test updating conversation id"""
        # Test with specific ID
        new_id = "new_id"
        self.multi_memory.update_conversation_id(new_id)
        self.assertEqual(self.multi_memory.default_conversation_id, new_id)
        
        # Test with None (should generate new UUID)
        self.multi_memory.update_conversation_id()
        self.assertNotEqual(self.multi_memory.default_conversation_id, new_id)
        # Should be a valid UUID
        uuid.UUID(self.multi_memory.default_conversation_id)
        
    def test_add_and_get_memory(self):
        """Test adding and retrieving memories"""
        # Test with default conversation
        self.multi_memory.add(memories=self.test_message)
        memories = self.multi_memory.get()
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0].content, "test content")
        
        # Test with specific conversation
        conv_id = "test_conv"
        self.multi_memory.add(memories=self.test_message, conversation_id=conv_id)
        memories = self.multi_memory.get(conversation_id=conv_id)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0].content, "test content")
        
    def test_get_memory_creates_new_instance(self):
        """Test that get_memory creates new instance if not exists"""
        conv_id = "new_conv"
        memory = self.multi_memory.get_memory(conv_id)
        self.assertIsNotNone(memory)
        self.assertEqual(memory.size(), 0)
        
    def test_delete_memory(self):
        """Test deleting memories"""
        # Add two messages
        self.multi_memory.add(memories=self.test_message)
        self.multi_memory.add(memories=Message(content="second message", role="user", name="test_user"))
        
        # Delete first message
        self.multi_memory.delete(index=0)
        memories = self.multi_memory.get()
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0].content, "second message")
        
    def test_clear_specific_conversation(self):
        """Test clearing specific conversation"""
        conv_id = "test_conv"
        self.multi_memory.add(memories=self.test_message, conversation_id=conv_id)
        self.multi_memory.clear(conversation_id=conv_id)
        self.assertEqual(self.multi_memory.size(conversation_id=conv_id), 0)
        
    def test_clear_all_conversations(self):
        """Test clearing all conversations"""
        # Add memories to different conversations
        self.multi_memory.add(memories=self.test_message, conversation_id="conv1")
        self.multi_memory.add(memories=self.test_message, conversation_id="conv2")
        
        self.multi_memory.clear()
        self.assertEqual(self.multi_memory.size(), 0)
        self.assertEqual(len(self.multi_memory.get_all_conversations()), 0)
        
    def test_get_all_conversations(self):
        """Test getting all conversation IDs"""
        conv_ids = ["conv1", "conv2", "conv3"]
        for conv_id in conv_ids:
            self.multi_memory.add(memories=self.test_message, conversation_id=conv_id)
            
        all_convs = self.multi_memory.get_all_conversations()
        self.assertEqual(len(all_convs), len(conv_ids))
        for conv_id in conv_ids:
            self.assertIn(conv_id, all_convs)
            
    def test_size(self):
        """Test size calculations"""
        # Test size of specific conversation
        conv_id = "test_conv"
        self.multi_memory.add(conversation_id=conv_id, memories=self.test_message)
        self.assertEqual(self.multi_memory.size(conversation_id=conv_id), 1)
        
        # Test total size across all conversations
        self.multi_memory.add(conversation_id="other_conv", memories=self.test_message)
        self.assertEqual(self.multi_memory.size(), 2)
        
        # Test size of non-existent conversation
        self.assertEqual(self.multi_memory.size(conversation_id="non_existent"), 0)
        
    def test_add_multiple_messages(self):
        """Test adding multiple messages at once"""
        messages: List[Message] = [
            Message(content=f"message {i}", role="user", name="test_user")
            for i in range(3)
        ]
        
        self.multi_memory.add(memories=messages)
        retrieved = self.multi_memory.get()
        self.assertEqual(len(retrieved), 3)
        for i, msg in enumerate(retrieved):
            self.assertEqual(msg.content, f"message {i}")
            
    def test_get_with_recent_n(self):
        """Test getting recent n memories"""
        messages = [
            Message(content=f"message {i}", role="user", name="test_user")
            for i in range(5)
        ]
        self.multi_memory.add(memories=messages)
        
        recent = self.multi_memory.get(recent_n=3)
        self.assertEqual(len(recent), 3)
        for i, msg in enumerate(recent):
            self.assertEqual(msg.content, f"message {i+2}")
            
    def test_get_with_filter(self):
        """Test getting memories with filter function"""
        messages = [
            Message(content=f"message {i}", 
                   role="user" if i % 2 == 0 else "assistant",
                   name="test_user" if i % 2 == 0 else "assistant")
            for i in range(4)
        ]
        self.multi_memory.add(memories=messages)
        
        # Filter for user messages only
        user_messages = self.multi_memory.get(
            filter_func=lambda i, m: m.role == "user"
        )
        self.assertEqual(len(user_messages), 2)
        for msg in user_messages:
            self.assertEqual(msg.role, "user")
            self.assertEqual(msg.name, "test_user")

    def test_load_from_hub(self, mock_hub_client):
        """Test loading memories from hub for a specific conversation"""
        # Prepare test data
        conv_id = "test_conv"
        test_memories = [
            Message(content="hub message 1", role="user", name="test_user"),
            Message(content="hub message 2", role="assistant", name="assistant")
        ]
        mock_hub_client.load_from_hub.return_value = test_memories
        
        # Test loading with specific conversation ID
        self.multi_memory.load_from_hub(conv_id)
        mock_hub_client.load_from_hub.assert_called_with(
            "test_account", conv_id, self.multi_memory.get_memory(conv_id), False
        )
        
        # Test loading with default conversation ID
        self.multi_memory.load_from_hub()
        mock_hub_client.load_from_hub.assert_called_with(
            "test_account", 
            self.multi_memory.default_conversation_id,
            self.multi_memory.get_memory(),
            False
        )
        
        # Test loading with overwrite=True
        self.multi_memory.load_from_hub(conv_id, overwrite=True)
        mock_hub_client.load_from_hub.assert_called_with(
            "test_account", conv_id, self.multi_memory.get_memory(conv_id), True
        )
        
    def test_load_all_from_hub(self, mock_hub_client):
        """Test loading all memories from hub"""
        # Prepare test data
        test_conversations = ["conv1", "conv2", "conv3"]
        mock_hub_client.list_conversations.return_value = test_conversations
        
        # Test loading all conversations
        self.multi_memory.load_all_from_hub()
        
        # Verify list_conversations was called
        mock_hub_client.list_conversations.assert_called_once_with("test_account")
        
        # Verify load_from_hub was called for each conversation
        self.assertEqual(mock_hub_client.load_from_hub.call_count, len(test_conversations))
        for conv_id in test_conversations:
            mock_hub_client.load_from_hub.assert_any_call(
                "test_account", conv_id, self.multi_memory.get_memory(conv_id), False
            )
            
        # Test loading all conversations with overwrite=True
        mock_hub_client.load_from_hub.reset_mock()
        self.multi_memory.load_all_from_hub(overwrite=True)
        
        for conv_id in test_conversations:
            mock_hub_client.load_from_hub.assert_any_call(
                "test_account", conv_id, self.multi_memory.get_memory(conv_id), True
            )

if __name__ == '__main__':
    unittest.main() 