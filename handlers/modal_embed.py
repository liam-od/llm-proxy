"""Embeddings backed by the deployed Modal `Embedder` class, over RPC.

The Embedder is a Modal class with no HTTP endpoint, so it can't be reached as an
OpenAI-compatible URL like the vLLM containers. This CustomLLM bridges the
proxy's `/v1/embeddings` to `Embedder.embed_documents.remote(...)`. Modal auth is
read from `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` in the environment.

Query-side instruction prompting (the prototype's `embed_query`) is the caller's
job: prepend the instruction to the text before sending it here, so this stays a
plain text -> vector endpoint.
"""

import modal
from litellm.llms.custom_llm import CustomLLM
from litellm.types.utils import EmbeddingResponse

_APP_NAME = "pensieve"
_CLASS_NAME = "Embedder"
_embedder = None


def _get_embedder():
    """Resolve the deployed Embedder lazily (a network lookup), then cache it."""
    global _embedder
    if _embedder is None:
        _embedder = modal.Cls.from_name(_APP_NAME, _CLASS_NAME)()
    return _embedder


def _fill(model_response: EmbeddingResponse, model: str, vectors: list) -> EmbeddingResponse:
    model_response.model = model
    model_response.object = "list"
    model_response.data = [
        {"object": "embedding", "index": i, "embedding": vec}
        for i, vec in enumerate(vectors)
    ]
    return model_response


def _texts(input) -> list:
    return input if isinstance(input, list) else [input]


class ModalEmbedder(CustomLLM):
    """Routes `/v1/embeddings` to the Modal Embedder's `embed_documents` RPC."""

    def embedding(self, model, input, model_response, **kwargs) -> EmbeddingResponse:
        vectors = _get_embedder().embed_documents.remote(_texts(input))
        return _fill(model_response, model, vectors)

    async def aembedding(self, model, input, model_response, **kwargs) -> EmbeddingResponse:
        # .remote.aio() keeps the proxy's event loop free during the RPC.
        vectors = await _get_embedder().embed_documents.remote.aio(_texts(input))
        return _fill(model_response, model, vectors)


modal_embedder = ModalEmbedder()
