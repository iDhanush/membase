# -*- coding: utf-8 -*-
"""
MultiMemory module for managing multiple BufferedMemory instances
"""

from typing import Optional, Dict, List, Union, Callable
import uuid
from .buffered_memory import BufferedMemory
from .message import Message

class MultiMemory:
    """
    A class that manages multiple BufferedMemory instances, distinguished by conversation_id
    """
    
    def __init__(self, membase_account: str = "default", auto_upload_to_hub: bool = False, default_conversation_id: Optional[str] = None):
        """
        Initialize MultiMemory

        Args:
            membase_account (str): The membase account name
            auto_upload_to_hub (bool): Whether to automatically upload to hub
            default_conversation_id (Optional[str]): The default conversation ID. If None, generates a new UUID.
        """
        self._memories: Dict[str, BufferedMemory] = {}
        self._membase_account = membase_account
        self._auto_upload_to_hub = auto_upload_to_hub
        self._default_conversation_id = default_conversation_id or str(uuid.uuid4())
        
    def update_conversation_id(self, conversation_id: Optional[str] = None) -> None:
        """
        Update the default conversation ID. If conversation_id is None, generates a new UUID.

        Args:
            conversation_id (Optional[str]): The new default conversation ID. If None, generates a new UUID.
        """
        self._default_conversation_id = conversation_id or str(uuid.uuid4())
        
    def get_memory(self, conversation_id: Optional[str] = None) -> BufferedMemory:
        """
        Get BufferedMemory instance for the specified conversation_id.
        Creates a new instance if it doesn't exist.

        Args:
            conversation_id (Optional[str]): The conversation ID. If None, uses default ID.

        Returns:
            BufferedMemory: The corresponding memory instance
        """
        if conversation_id is None:
            conversation_id = self._default_conversation_id
            
        if conversation_id not in self._memories:
            self._memories[conversation_id] = BufferedMemory(
                conversation_id=conversation_id,
                membase_account=self._membase_account,
                auto_upload_to_hub=self._auto_upload_to_hub
            )
        return self._memories[conversation_id]
    
    def add(self, conversation_id: Optional[str] = None, memories: Union[List[Message], Message, None] = None) -> None:
        """
        Add memories to the specified conversation

        Args:
            conversation_id (Optional[str]): The conversation ID. If None, uses default ID.
            memories: The memories to add
        """
        memory = self.get_memory(conversation_id)
        memory.add(memories)
        
    def get(self, conversation_id: Optional[str] = None, recent_n: Optional[int] = None,
            filter_func: Optional[Callable[[int, dict], bool]] = None) -> list:
        """
        Get memories from the specified conversation

        Args:
            conversation_id (Optional[str]): The conversation ID. If None, uses default ID.
            recent_n (Optional[int]): Number of recent memories to retrieve
            filter_func (Optional[Callable]): Filter function for memories

        Returns:
            list: List of memories
        """
        memory = self.get_memory(conversation_id)
        return memory.get(recent_n=recent_n, filter_func=filter_func)
        
    def delete(self, conversation_id: Optional[str] = None, index: Union[List[int], int] = None) -> None:
        """
        Delete memories from the specified conversation

        Args:
            conversation_id (Optional[str]): The conversation ID. If None, uses default ID.
            index: Index or indices of memories to delete
        """
        if conversation_id is None:
            conversation_id = self._default_conversation_id
            
        if conversation_id in self._memories:
            self._memories[conversation_id].delete(index)
            
    def clear(self, conversation_id: Optional[str] = None) -> None:
        """
        Clear memories from the specified conversation.
        If conversation_id is None, clears all memories.

        Args:
            conversation_id (Optional[str]): The conversation ID. If None, clears all conversations.
        """
        if conversation_id is None:
            self._memories.clear()
            self._default_conversation_id = str(uuid.uuid4())
        elif conversation_id in self._memories:
            self._memories[conversation_id].clear()
            
    def get_all_conversations(self) -> List[str]:
        """
        Get all conversation IDs

        Returns:
            List[str]: List of conversation IDs
        """
        return list(self._memories.keys())
    
    def size(self, conversation_id: Optional[str] = None) -> int:
        """
        Get the number of memories

        Args:
            conversation_id (Optional[str]): The conversation ID.
                If None, returns total count of memories across all conversations.

        Returns:
            int: Number of memories
        """
        if conversation_id is None:
            return sum(memory.size() for memory in self._memories.values())
        elif conversation_id in self._memories:
            return self._memories[conversation_id].size()
        return 0
        
    @property
    def default_conversation_id(self) -> str:
        """
        Get the default conversation ID

        Returns:
            str: The default conversation ID
        """
        return self._default_conversation_id
