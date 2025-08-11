# -*- coding: utf-8 -*-
"""
Modelos para el sistema de errores comunes
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ErrorCategory(Enum):
    """Categorías de errores"""
    NAVIGATION = "navigation"
    SELECTOR = "selector"
    EXTRACTION = "extraction"
    SEARCH = "search"
    PAGINATION = "pagination"
    BROWSER = "browser"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severidad del error"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorPattern:
    """Patrón de error identificado"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    error_message: str
    original_error: str
    context_info: Dict[str, Any]
    solution: Optional[str] = None
    prevention_tips: List[str] = field(default_factory=list)
    frequency: int = 1
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    tool_name: Optional[str] = None
    page_type: Optional[str] = None
    query_context: Optional[str] = None


@dataclass
class ErrorStatistics:
    """Estadísticas de errores"""
    total_errors: int
    errors_by_category: Dict[str, int]
    errors_by_severity: Dict[str, int]
    most_common_errors: List[Dict[str, Any]]
    recent_errors: List[Dict[str, Any]]
    learning_suggestions: List[str]


@dataclass
class ErrorRecommendation:
    """Recomendación basada en errores comunes"""
    recommendation_id: str
    title: str
    description: str
    related_errors: List[str]
    prevention_steps: List[str]
    applicable_contexts: List[str]
    priority: int = 1