"""LLM service for SQL generation using pretrained transformer models"""

from pathlib import Path
import logging
import re
from typing import Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

try:
    from peft import PeftModel
except ImportError:  # pragma: no cover - dependency handling
    PeftModel = None

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating SQL using a pretrained language model"""

    def __init__(
        self,
        model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        adapter_path: Optional[str] = None,
        load_in_4bit: bool = False
    ):
        """
        Initialize LLM service with a pretrained model.

        Args:
            model_name: HuggingFace model identifier
            adapter_path: Optional local path to LoRA adapters
            load_in_4bit: Whether to use 4-bit quantization for GPU inference
        """
        self.model_name = model_name
        self.adapter_path = adapter_path
        self.load_in_4bit = load_in_4bit
        self.tokenizer = None
        self.model = None
        self.device = None
        logger.info(
            "LLMService initialized with model=%s, adapter_path=%s, load_in_4bit=%s",
            model_name,
            adapter_path,
            load_in_4bit
        )

    @staticmethod
    def _is_adapter_dir(path: Path) -> bool:
        """Check whether a directory looks like a PEFT adapter folder."""
        return (
            path.is_dir()
            and (path / "adapter_config.json").exists()
            and (path / "adapter_model.safetensors").exists()
        )

    @staticmethod
    def _resolve_adapter_path(adapter_path: str) -> Optional[Path]:
        """Resolve an adapter path against common project locations."""
        raw_path = Path(adapter_path)
        candidates = [raw_path]

        project_root = Path(__file__).resolve().parents[2]
        candidates.append(project_root / raw_path)

        # Common fallback: zip extracted directly to `models/` instead of `models/lora_adapters/`.
        if raw_path.name == "lora_adapters":
            candidates.append(raw_path.parent)
            candidates.append(project_root / raw_path.parent)

        for candidate in candidates:
            if candidate.exists() and LLMService._is_adapter_dir(candidate):
                return candidate.resolve()

        return None

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

            model_kwargs = {}
            if self.device == "cuda":
                model_kwargs["device_map"] = "auto"
                if self.load_in_4bit:
                    model_kwargs["load_in_4bit"] = True
                else:
                    model_kwargs["torch_dtype"] = torch.float16
            else:
                if self.load_in_4bit:
                    logger.warning("4-bit loading requested but CUDA is unavailable. Falling back to CPU fp32.")
                model_kwargs["torch_dtype"] = torch.float32

            base_model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )

            self.model = base_model
            if self.adapter_path:
                if PeftModel is None:
                    raise ImportError(
                        "peft is not installed. Install it with `pip install peft` "
                        "to load LoRA adapters."
                    )

                resolved_adapter_path = self._resolve_adapter_path(self.adapter_path)
                if not resolved_adapter_path:
                    raise FileNotFoundError(
                        f"LoRA adapter path not found: {self.adapter_path}"
                    )

                logger.info("Applying LoRA adapters from: %s", resolved_adapter_path)
                self.model = PeftModel.from_pretrained(base_model, str(resolved_adapter_path))

            self.model.eval()

            logger.info(
                "Model loaded successfully on %s (adapter=%s)",
                self.device,
                bool(self.adapter_path)
            )
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
