#!/usr/bin/env bash
# Explanation Protocol Stop hook entrypoint. See explanation-terms.py.
exec /usr/bin/env python3 "$(dirname "$0")/explanation-terms.py"
