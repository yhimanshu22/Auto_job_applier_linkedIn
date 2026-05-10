"""
Backward-compatible entrypoint.

The implementation lives in the `run_ai_bot` package; this module preserves
`from runAiBot import main` and `python runAiBot.py` for server.py --bot and docs.
"""

from run_ai_bot.main import main

if __name__ == "__main__":
    main()
