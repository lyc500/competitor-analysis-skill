"""Deprecated import shim for the bounded legacy/demo parser.

Formal work uses ``--task-file`` and does not call this module.  The alias is
kept so existing demo scripts importing ``parse_request`` continue to run.
"""

from .legacy_demo import parse_legacy_demo_request


parse_request = parse_legacy_demo_request

__all__ = ["parse_request", "parse_legacy_demo_request"]
