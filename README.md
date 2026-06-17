# llm-proxy
A simple implementation of a [LiteLLM](https://github.com/BerriAI/litellm) proxy server with custom handlers.
As an example I've added a custom handler that calls the Claude Code CLI so that we can still make requests
with OAuth. This lets us still test side projects with our claude account and get the most out of our usage.

You used to be able to call claude with `--bare` that would remove all the extras that come with claude code
and essentially just make an api call, but that now strips the auth. We are left with a slower model call,
but on the upside we get the full agent experience with tool calls.


## Requirements

- [uv](https://docs.astral.sh/uv/)
- [Claude Code CLI](https://claude.ai/code) (`claude` on your PATH, authenticated)

## Usage

Start the proxy on port 4001 (see Makefile) with `make serve` and run tests with `make test`.
`make auth` (re)authenticates the GitHub Copilot model (`mini`) via GitHub's device-code login.

The server exposes an OpenAI-compatible endpoint at `http://localhost:4001/v1`. Any OpenAI SDK
client can point at it:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:4001/v1", api_key="anything")

response = client.chat.completions.create(
    model="haiku",
    messages=[{"role": "user", "content": "hello"}],
)
print(response.choices[0].message.content)
```

Or with Pydantic AI:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    "haiku",
    provider=OpenAIProvider(base_url="http://localhost:4001/v1", api_key="anything"),
)
agent = Agent(model)

result = agent.run_sync("hello")
print(result.output)
```

Or with LangChain:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="haiku",
    base_url="http://localhost:4001/v1",
    api_key="anything",
)

response = llm.invoke("hello")
print(response.content)
```

## Configuration

Proxy settings live in [`config.yaml`](./config.yaml). Each entry under `model_list` defines a public
alias (`model_name`) that clients pass as `model="..."`, mapped to a `<provider>/<model>` routing
string in `litellm_params.model`. Custom providers are registered under
`litellm_settings.custom_provider_map`, pointing at a `CustomLLM` instance. The Claude Code handler
lives in [`handlers/claude.py`](./handlers/claude.py).

To add a new alias, add an entry to `model_list`. To add a new backend, write a `CustomLLM`
subclass and register it under a new `provider` name.

## Modal-backed aliases (Pensieve inference)

Three aliases front the deployed `pensieve` Modal app, so any OpenAI client gets transcription,
chat, and embeddings without touching Modal:

| alias | endpoint | backend |
| --- | --- | --- |
| `modal-llm` | `POST /v1/chat/completions` | the `pensieve-llm` vLLM server (HTTP) |
| `modal-transcribe` | `POST /v1/audio/transcriptions` | the `pensieve-transcribe` vLLM server (HTTP) |
| `modal-embed` | `POST /v1/embeddings` | the `Embedder` Modal class, via RPC ([`handlers/modal_embed.py`](./handlers/modal_embed.py)) |

The embedder has no HTTP endpoint (it's a Modal class, not a web server), so `modal-embed` is a
`CustomLLM` that calls `Embedder.embed_documents.remote(...)`. This is the only piece that needs
Modal credentials — clients never do.

Required environment (the proxy holds the secrets; clients see none of them):

```bash
VLLM_API_KEY=        # bearer for the two vLLM endpoints
MODAL_TOKEN_ID=      # Modal auth for the embedder RPC (from `modal token current`)
MODAL_TOKEN_SECRET=
```

## Docker

```bash
docker build -t llm-proxy .
docker run -p 4001:4001 --env-file .env llm-proxy   # .env holds the vars above
```

The image serves only the Modal aliases (the `claude-code` ones need the `claude` CLI, absent here).

## Securing a hosted deployment

By default the proxy is open (clients send `api_key="anything"`). When you expose it, set a master
key so callers can't burn your Modal/GPU credits — add to `config.yaml`:

```yaml
general_settings:
  master_key: os.environ/PROXY_MASTER_KEY
```

and pass `PROXY_MASTER_KEY` in the environment; clients then send it as their API key.

