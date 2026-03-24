"""Abstract base class for all pluggable refactoring heuristic rules."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import FileTokenInfo, RefactorRecommendation


class RefactorRule(ABC):
    """Base class for a single refactoring heuristic rule.

    Subclasses must implement :meth:`applies_to` and :meth:`evaluate`.
    The two-method design allows the engine to skip the (potentially
    expensive) evaluation phase when a rule is not applicable to a
    given file type.
    """

    @abstractmethod
    def applies_to(self, file_info: FileTokenInfo) -> bool:
        """Return True if this rule should be evaluated for *file_info*.

        This is a cheap guard evaluated before reading the file from disk.
        """
        ...

    @abstractmethod
    def evaluate(
        self,
        file_info: FileTokenInfo,
        project_path: str,
    ) -> list[RefactorRecommendation]:
        """Run the rule against *file_info* and return recommendations.

        Parameters
        ----------
        file_info:
            Token-annotated metadata for the file.
        project_path:
            Absolute path to the project root.  Use
            ``os.path.join(project_path, file_info.path)`` to resolve the
            absolute file path.

        Returns
        -------
        list[RefactorRecommendation]
            Zero or more actionable recommendations.  The list is empty when
            the rule finds no issues.
        """
        ...
