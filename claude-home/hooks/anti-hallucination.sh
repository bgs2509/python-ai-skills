#!/usr/bin/env bash
# Anti-hallucination Stop hook entrypoint. See anti-hallucination.py.
exec /usr/bin/env python3 "$(dirname "$0")/anti-hallucination.py"
