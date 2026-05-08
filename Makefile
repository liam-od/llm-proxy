serve:
	@uv run litellm --config config.yaml --port 4001

test:
	@uv run python tests/test.py
