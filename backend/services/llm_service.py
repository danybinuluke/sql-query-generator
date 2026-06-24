"""LLM service for SQL generation using Groq API"""

import os
import logging
import re
from typing import Optional, Tuple

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating SQL using Groq API"""

    def __init__(
        self,
        model_name: str = "llama3-70b-8192",
        adapter_path: Optional[str] = None,
        load_in_4bit: bool = False
    ):
        """
        Initialize LLM service.
        (adapter_path and load_in_4bit are ignored when using Groq API)
        """
        # We default to llama3-70b-8192 if the default was set to something else previously
        if "llama" not in model_name.lower() and "mixtral" not in model_name.lower() and "gemma" not in model_name.lower():
            self.model_name = "llama3-70b-8192"
        else:
            self.model_name = model_name
            
        self.client = None
        logger.info("LLMService initialized with Groq model=%s", self.model_name)

    def load_model(self) -> bool:
        """
        Initialize the Groq client.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Initializing Groq client...")
            api_key = os.environ.get("GROQ_API_KEY")
            
            if not api_key:
                logger.error("GROQ_API_KEY environment variable is not set!")
                return False
                
            if Groq is None:
                logger.error("groq package is not installed. Run `pip install groq`.")
                return False

            self.client = Groq(api_key=api_key)
            logger.info("Groq client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Groq client: {e}")
            return False

    def generate_sql(self, prompt: str, max_tokens: int = 1024) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate SQL from a prompt using the Groq API.

        Args:
            prompt: Full prompt including system instructions and schema
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (success, generated_sql, error_message)
        """
        if not self.client:
            return False, None, "Groq client not initialized"

        try:
            # Generate with Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model_name,
                temperature=0.1,
                max_tokens=max_tokens,
                top_p=0.9,
                stream=False,
            )

            # Extract response
            response = chat_completion.choices[0].message.content

            # Extract SQL from response
            sql = self._extract_sql(response, prompt)

            if not sql:
                return False, None, "Could not extract SQL from model output"

            logger.info(f"Generated SQL: {sql[:100]}...")
            return True, sql, None

        except Exception as e:
            logger.error(f"Unexpected error during Groq generation: {e}")
            return False, None, f"Unexpected error: {str(e)}"

    def _extract_sql(self, response: str, original_prompt: str) -> Optional[str]:
        """
        Extract SQL query from model response.
        """
        # Try to extract from ```sql code blocks
        sql_block_match = re.search(r"```sql\s*([\s\S]*?)```", response, re.IGNORECASE)
        if sql_block_match:
            sql = sql_block_match.group(1).strip()
            if sql:
                return sql

        # Try to extract from generic ``` code blocks
        code_block_match = re.search(r"```\s*([\s\S]*?)```", response)
        if code_block_match:
            sql = code_block_match.group(1).strip()
            if sql and sql.strip().upper().startswith(("SELECT", "WITH")):
                return sql

        # If response contains SQL directly, extract it
        lines = response.strip().split("\n")
        for i, line in enumerate(lines):
            if line.strip().upper().startswith(("SELECT", "WITH")):
                # Found SQL start, collect until semicolon or end
                sql_lines = [line]
                for j in range(i + 1, len(lines)):
                    sql_lines.append(lines[j])
                    if ";" in lines[j]:
                        break

                sql = "\n".join(sql_lines).strip()
                return sql

        return None

    def unload_model(self) -> None:
        """Release client (not strictly needed for API)"""
        self.client = None
        logger.info("Groq client disconnected")

    def is_loaded(self) -> bool:
        """Check if client is initialized"""
        return self.client is not None

    def __enter__(self):
        """Context manager support"""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.unload_model()
