"""Enum definitions for ContextRefactor domain models."""

from __future__ import annotations

import enum


class FileCategory(enum.StrEnum):
    """High-level file classification used to route analysis."""

    SOURCE_CODE = "source_code"
    MARKDOWN = "markdown"
    CONFIGURATION = "configuration"
    BINARY = "binary"
    OTHER = "other"


class CodeSmell(enum.StrEnum):
    """Detectable code smells (subset of Fowler / refactoring.guru catalog)."""

    LONG_METHOD = "Long Method"
    LARGE_CLASS = "Large Class"
    LONG_PARAMETER_LIST = "Long Parameter List"
    DUPLICATE_CODE = "Duplicate Code"
    DEEP_NESTING = "Deep Nesting"
    GOD_FILE = "God File"
    MIXED_RESPONSIBILITIES = "Mixed Responsibilities"
    POOR_NAMING = "Poor Naming"
    HIGH_COUPLING = "High Coupling"


class RefactorTechnique(enum.StrEnum):
    """Refactoring techniques from https://refactoring.guru/refactoring/techniques."""

    EXTRACT_METHOD = "Extract Method"
    EXTRACT_CLASS = "Extract Class"
    MOVE_METHOD = "Move Method"
    MOVE_FIELD = "Move Field"
    RENAME_METHOD = "Rename Method"
    EXTRACT_VARIABLE = "Extract Variable"
    REPLACE_TEMP_WITH_QUERY = "Replace Temp with Query"
    DECOMPOSE_CONDITIONAL = "Decompose Conditional"
    SPLIT_DOCUMENT = "Split Document"
    EXTRACT_MODULE = "Extract Module"
    RENAME_VARIABLE = "Rename Variable"
    INVERT_DEPENDENCY = "Invert Dependency"
    INTRODUCE_INTERFACE = "Introduce Interface"


class Priority(enum.StrEnum):
    """Priority level for refactoring recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DependencyKind(enum.StrEnum):
    """Classification of a dependency relationship."""

    IMPORT = "import"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    TYPE_USAGE = "type_usage"
    DECORATOR = "decorator"


class DependencyScope(enum.StrEnum):
    """Whether a dependency is internal to the project or external."""

    INTERNAL = "internal"
    EXTERNAL = "external"
