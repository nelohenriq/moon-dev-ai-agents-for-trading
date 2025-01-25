"""
🌙 Moon Dev's Strategies Package
"""

from .base_strategy import BaseStrategy
from .example_strategy import SimpleMAStrategy

# We only need to export BaseStrategy - custom strategies will be loaded dynamically
__all__ = ['BaseStrategy', 'SimpleMAStrategy'] 