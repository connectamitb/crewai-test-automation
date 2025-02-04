from contextlib import contextmanager
from typing import Generator
import logging

class BaseAgent:
    """Base class for all agents with common functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @contextmanager
    def memory_context(self) -> Generator:
        """Context manager for memory efficient operations"""
        try:
            yield
        finally:
            # Clean up any temporary memory/resources
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources after task execution"""
        # Implement cleanup logic
        pass 