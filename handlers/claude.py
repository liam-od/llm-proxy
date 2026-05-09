import subprocess

from litellm.llms.custom_llm import CustomLLM
from litellm.types.utils import Choices, Message, ModelResponse, Usage

EFFORT_BY_MODEL = {
    "sonnet": "medium",
    "opus": "high",
}


class ClaudeCodeLLM(CustomLLM):
    """Runs the claude-code CLI binary as a completion backend.

    The model name is taken from each request, so a single instance serves
    haiku/sonnet/opus. Reasoning effort is looked up per model.
    """

    def _build_prompt(self, messages: list) -> str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in messages)

    def _resolve_model(self, model: str) -> str:
        return model.split("/", 1)[1] if "/" in model else model

    def _run(self, model: str, messages: list) -> str:
        resolved = self._resolve_model(model)
        cmd = ["claude", "-p", self._build_prompt(messages), "--model", resolved]
        if effort := EFFORT_BY_MODEL.get(resolved):
            cmd += ["--effort", effort]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def _build_response(self, model: str, text: str) -> ModelResponse:
        return ModelResponse(
            model=model,
            choices=[Choices(finish_reason="stop", message=Message(role="assistant", content=text))],
            usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        )

    def completion(self, model: str, messages: list, **kwargs) -> ModelResponse:
        return self._build_response(model, self._run(model, messages))

    async def acompletion(self, model: str, messages: list, **kwargs) -> ModelResponse:
        return self.completion(model=model, messages=messages, **kwargs)


claude_code = ClaudeCodeLLM()
