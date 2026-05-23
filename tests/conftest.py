"""Pytest configuration and fixtures"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys


# Setup mocks before importing backend modules
def pytest_configure(config):
    """Configure pytest and setup mocks before tests run"""
    # Mock transformer models
    mock_tokenizer = MagicMock()
    mock_model = MagicMock()
    mock_model.eval = MagicMock(return_value=None)

    patcher_tokenizer = patch("backend.services.llm_service.AutoTokenizer.from_pretrained", return_value=mock_tokenizer)
    patcher_model = patch("backend.services.llm_service.AutoModelForCausalLM.from_pretrained", return_value=mock_model)
    patcher_cuda = patch("torch.cuda.is_available", return_value=False)
    patcher_torch_no_grad = patch("backend.services.llm_service.torch.no_grad")

    patcher_tokenizer.start()
    patcher_model.start()
    patcher_cuda.start()
    patcher_torch_no_grad.start()

    config.addinivalue_line("markers", "slow: mark test as slow")


@pytest.fixture(autouse=True)
def mock_llm_generation(request, monkeypatch):
    """Mock LLM generation for all tests except LLM service tests"""
    # Don't mock LLM tests since they test the actual service
    if "test_llm_service" in request.node.nodeid:
        return

    from backend.services import LLMService

    def mock_generate(self, prompt, max_tokens=256):
        """Mock SQL generation that extracts table name from prompt"""
        # Extract a table name from the prompt to make SQL that works
        import re
        table_match = re.search(r"Table:\s*(\w+)", prompt, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1)
            return True, f"SELECT * FROM {table_name};", None
        # Fallback to COUNT query
        return True, "SELECT COUNT(*) as count;", None

    def mock_is_loaded(self):
        """Mock model loaded check"""
        return True

    monkeypatch.setattr(LLMService, "generate_sql", mock_generate)
    monkeypatch.setattr(LLMService, "is_loaded", mock_is_loaded)


