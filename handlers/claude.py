import subprocess

from litellm.llms.custom_llm import CustomLLM
from litellm.types.utils import Choices, Message, ModelResponse, Usage

EFFORT_SUPPORTED_MODELS = ("sonnet", "opus")


class ClaudeCodeLLM(CustomLLM):
    """Runs the claude-code CLI binary as a completion backend."""

    def __init__(self, model: str | None = None, effort: str | None = None):
        self._model = model
        self._effort = effort

    def _build_prompt(self, messages: list) -> str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in messages)

    def _run(self, messages: list) -> str:
        cmd = ["claude", "-p", self._build_prompt(messages)]
        if self._model:
            cmd += ["--model", self._model]
        if self._effort and self._model and any(m in self._model for m in EFFORT_SUPPORTED_MODELS):
            cmd += ["--effort", self._effort]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def _build_response(self, model: str, text: str) -> ModelResponse:
        return ModelResponse(
            model=model,
            choices=[Choices(finish_reason="stop", message=Message(role="assistant", content=text))],
            usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        )

    def completion(self, model: str, messages: list, **kwargs) -> ModelResponse:
        return self._build_response(model, self._run(messages))

    async def acompletion(self, model: str, messages: list, **kwargs) -> ModelResponse:
        return self.completion(model=model, messages=messages, **kwargs)


haiku = ClaudeCodeLLM(model="haiku")
sonnet = ClaudeCodeLLM(model="sonnet", effort="medium")
opus = ClaudeCodeLLM(model="opus", effort="high")
