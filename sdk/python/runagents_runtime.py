"""Backward-compatibility shim: ``import runagents_runtime`` resolves to ``runagents.runtime``.

This keeps existing code (including test_runtime.py mock patches like
``mock.patch("runagents_runtime.urllib.request.urlopen")``) working unchanged.
"""

import runagents.runtime as _rt  # noqa: F401
import sys

# Replace this module object in sys.modules so that attribute access
# (e.g. runagents_runtime.ApprovalRequired, runagents_runtime.urllib)
# resolves against the real runtime module.
sys.modules[__name__] = _rt
