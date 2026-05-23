"""LLM service for SQL generation using pretrained transformer models"""

import logging
import re
from typing import Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating SQL using a pretrained language model"""

    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        """
        Initialize LLM service with a pretrained model.

        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        logger.info(f"LLMService initialized with model: {model_name}")

    def load_model(self) -> bool:
        """
        Load the pretrained model and tokenizer.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading model {self.model_name}...")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )
            self.model.eval()

            logger.info(f"Model loaded successfully on {self.device}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def generate_sql(self, prompt: str, max_tokens: int = 256) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate SQL from a prompt using the LLM.

        Args:
            prompt: Full prompt including system instructions and schema
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (success, generated_sql, error_message)
        """
        if not self.model or not self.tokenizer:
            return False, None, "Model not loaded"

        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            # Generate with controlled parameters
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.3,
                    top_p=0.9,
                    do_sample=True,
                    num_beams=1,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            # Decode output
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract SQL from response
            sql = self._extract_sql(response, prompt)

            if not sql:
                return False, None, "Could not extract SQL from model output"

            logger.info(f"Generated SQL: {sql[:100]}...")
            return True, sql, None

        except RuntimeError as e:
            logger.error(f"CUDA/Runtime error during generation: {e}")
            return False, None, f"Generation error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}")
            return False, None, f"Unexpected error: {str(e)}"

    def _extract_sql(self, response: str, original_prompt: str) -> Optional[str]:
        """
        Extract SQL query from model response.

        Attempts to extract SQL from markdown code blocks or raw response.

        Args:
            response: Full model response
            original_prompt: Original prompt sent to model

        Returns:
            Extracted SQL query or None
        """
        # Remove the original prompt from response if present
        if response.startswith(original_prompt):
            response = response[len(original_prompt):].strip()

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
        """Release model from memory"""
        try:
            if self.model:
                del self.model
                self.model = None
            if self.tokenizer:
                self.tokenizer = None
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            logger.info("Model unloaded from memory")
        except Exception as e:
            logger.warning(f"Error unloading model: {e}")

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.tokenizer is not None

    def __enter__(self):
        """Context manager support"""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.unload_model()
