"""
cnc - Campus Network Control

A CLI tool and Python library for managing campus network authentication.

Public API:
- CampusNetClient: high-level orchestration interface
- NetworkState: network/authentication state enum
"""

from __future__ import annotations

from cnc.client import CampusNetClient
from cnc.probe import NetworkState

__all__ = [
    "CampusNetClient",
    "NetworkState",
]

__version__ = "0.1.0"
