"""Portable demos and curated evidence for the PDHG GPU/CPU benchmark study."""

from .generators import FAMILY_GENERATORS, generate_demo
from .validators import validate_instance

__all__ = ["FAMILY_GENERATORS", "generate_demo", "validate_instance"]
__version__ = "0.1.0"
