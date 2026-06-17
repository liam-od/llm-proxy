#!/usr/bin/env python
"""Re-authenticate the GitHub Copilot backend used by the `mini` alias.

Clears the cached token and runs GitHub's device-code login (prints a URL + code
to authorize). Needs an active Copilot subscription on the account you authorize.
Run via `make auth`.
"""

import logging
import os
import shutil

import litellm
from litellm.llms.github_copilot.authenticator import Authenticator

litellm.suppress_debug_info = True
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)

TOKEN_DIR = os.getenv(
    "GITHUB_COPILOT_TOKEN_DIR",
    os.path.expanduser("~/.config/litellm/github_copilot"),
)


def main() -> int:
    shutil.rmtree(TOKEN_DIR, ignore_errors=True)
    print("Starting GitHub Copilot device login…\n")
    try:
        Authenticator().get_api_key()
    except Exception as e:
        print(f"\n✗ Auth failed: {e}")
        print(
            "  Re-run `make auth` and authorize within ~60s with a "
            "Copilot-enabled GitHub account."
        )
        return 1
    print("\n✓ Authenticated. Restart `make serve` — `mini` will load.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
