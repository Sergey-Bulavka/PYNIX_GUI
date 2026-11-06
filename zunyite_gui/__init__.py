# Copyright 2026 Sergii V.Bulavka
# SPDX-License-Identifier: Apache-2.0

"""Canonical Zunyite GUI public namespace with PYNIX compatibility."""

import pynix_gui as _legacy
from pynix_gui import *  # noqa: F401,F403

__version__ = _legacy.__version__
__all__ = _legacy.__all__
