"""Testing skills for various application types.

Beyond Ralph bundles testing capabilities for common app types and
can autonomously discover/install additional testing frameworks.
"""

from typing import Literal

AppType = Literal[
    "api",      # REST/GraphQL APIs
    "web",      # Web applications (browser-based)
    "cli",      # Command-line applications
    "desktop",  # Desktop GUI applications
    "mobile",   # Mobile applications
    "game",     # Games and graphics applications
]
