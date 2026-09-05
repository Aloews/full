"""Exception hierarchy shared by every Kontur engine."""

from __future__ import annotations


class KonturError(Exception):
    """Base class for every error raised by Kontur."""


class MissingProvenanceError(KonturError):
    """Raised when an externally sourced fact arrives without source/date/confidence.

    Kontur never lets an un-sourced number reach a report: an unattributed
    "Share of Voice" is indistinguishable from an invented one.
    """


class InvalidProvenanceError(KonturError):
    """Raised when provenance exists but is malformed (empty source, future date, ...)."""


class SampleDataError(KonturError):
    """Raised when sample/demo data is used where only real measurements are allowed."""


class UnprovenClaimError(KonturError):
    """Raised when an effect claim is made without a linked experiment result."""


class InsufficientDataError(KonturError):
    """Raised when a metric is requested but the input does not meet the minimum sample."""


class UnknownRuleError(KonturError):
    """Raised when a decision references a rule id that is not in the registry."""


class ConfigurationError(KonturError):
    """Raised when engine configuration is inconsistent (bad thresholds, unknown facet, ...)."""
