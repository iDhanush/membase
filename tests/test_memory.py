# -*- coding: utf-8 -*-
"""
Unit tests for memory classes and functions
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from membase.memory.message import Message
from membase.memory.buffered_memory import BufferedMemory
from membase.memory.serialize import serialize


class BufferedMemoryTest(unittest.TestCase):
    """
    Test cases for BufferedMemory
    """

    def setUp(self) -> None:
        self.memory = BufferedMemory(auto_upload_to_hub=True)
        self.file_name_1 = "tmp_mem_file1.txt"
        self.file_name_2 = "tmp_mem_file2.txt"
        self.Message_1 = Message("user", "Hello", role="user")
        self.Message_2 = Message(
            "agent",
            "Hello! How can I help you?",
            role="assistant",
            metadata="md"
        )
        self.Message_3 = Message(
            "user",
            "Translate the following sentence",
            role="assistant",
            metadata={"meta": "test"}
        )

        self.invalid = {"invalid_key": "invalid_value"}

    def tearDown(self) -> None:
        """Clean up before & after tests."""
        if os.path.exists(self.file_name_1):
            os.remove(self.file_name_1)
        if os.path.exists(self.file_name_2):
            os.remove(self.file_name_2)

    def test_add(self) -> None:
        """Test add different types of object"""
        # add Message
        self.memory.add(self.Message_1)
        self.assertEqual(
            self.memory.get(),
            [self.Message_1],
        )

        # add list
        self.memory.add([self.Message_2, self.Message_3])
        self.assertEqual(
            self.memory.get(),
            [self.Message_1, self.Message_2, self.Message_3],
        )

    @patch("loguru.logger.warning")
    def test_delete(self, mock_logging: MagicMock) -> None:
        """Test delete operations"""
        self.memory.add([self.Message_1, self.Message_2, self.Message_3])

        self.memory.delete(index=0)
        self.assertEqual(
            self.memory.get(),
            [self.Message_2, self.Message_3],
        )

        # test invalid
        self.memory.delete(index=100)
        mock_logging.assert_called_once_with(
            "Skip delete operation for the invalid index [100]",
        )

    def test_invalid(self) -> None:
        """Test invalid operations for memory"""
        # test invalid add
        with self.assertRaises(Exception) as context:
            self.memory.add(self.invalid)
        self.assertTrue(
            f"Cannot add {type(self.invalid)} to memory, must be a Message object."
            in str(context.exception),
        )

    def test_load_export(self) -> None:
        """
        Test load and export function of BufferedMemory
        """
        memory = BufferedMemory()
        user_input = Message(name="user", content="Hello", role="user")
        agent_input = Message(
            name="agent",
            content="Hello! How can I help you?",
            role="assistant",
        )
        memory.load([user_input, agent_input])
        retrieved_mem = memory.export(to_mem=True)
        self.assertEqual(
            retrieved_mem,
            [user_input, agent_input],
        )

        memory.export(file_path=self.file_name_1)
        memory.clear()
        self.assertEqual(
            memory.get(),
            [],
        )
        memory.load(self.file_name_1, True)
        self.assertEqual(
            serialize(memory.get()),
            serialize([user_input, agent_input]),
        )

    def test_get_by_name(self) -> None:
        """Test retrieving memories by name using filter_func"""
        # Add messages with different names
        self.memory.add([
            Message("user1", "Hello from user1", role="user"),
            Message("user2", "Hello from user2", role="user"),
            Message("user1", "Another message from user1", role="user"),
            Message("agent", "Response from agent", role="assistant")
        ])
        
        # Test getting all messages from user1 using filter_func
        def name_filter(_, memory):
            return memory.name == "user1"
        user1_messages = self.memory.get(filter_func=name_filter)
        self.assertEqual(len(user1_messages), 2)
        self.assertTrue(all(msg.name == "user1" for msg in user1_messages))
        
        # Test getting recent messages from user1
        recent_user1 = self.memory.get(recent_n=2, filter_func=name_filter)
        self.assertEqual(len(recent_user1), 1)
        self.assertEqual(recent_user1[0].content, "Another message from user1")
        
        # Test getting messages from non-existent name
        def nonexistent_filter(_, memory):
            return memory.name == "nonexistent"
        empty_messages = self.memory.get(filter_func=nonexistent_filter)
        self.assertEqual(len(empty_messages), 0)
        
        # Test getting messages from agent
        def agent_filter(_, memory):
            return memory.name == "agent"
        agent_messages = self.memory.get(filter_func=agent_filter)
        self.assertEqual(len(agent_messages), 1)
        self.assertEqual(agent_messages[0].content, "Response from agent")


if __name__ == "__main__":
    unittest.main()
