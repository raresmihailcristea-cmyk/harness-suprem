#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Capture-auth shim — delegates to scion_harness.capture_auth_main()

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scion_harness

if __name__ == "__main__":
    sys.exit(scion_harness.capture_auth_main())
