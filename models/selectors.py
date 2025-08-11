from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class SelectorTest:
    """Resultado de prueba de selector"""
    selector: str
    found_elements: int
    visible_elements: int
    sample_text: Optional[str] = None
    is_valid: bool = False
    recommendations: Optional[List[str]] = None


@dataclass
class DiscoveredSelector:
    """Selector descubierto con metadatos"""
    selector: str
    confidence: float
    description: str
    element_count: int


@dataclass
class SelectorAnalysis:
    """Análisis detallado de un selector"""
    element_count: int
    visible_elements: int
    sample_texts: List[Dict[str, Any]]
    element_types: List[str]
    has_useful_content: bool


@dataclass
class SelectorTestResult:
    """Resultado completo de prueba de selector"""
    selector: str
    success: bool
    element_count: int
    analysis: Optional[SelectorAnalysis] = None
    utility_score: float = 0.0
    recommendations: Optional[List[str]] = None
    is_useful: bool = False
    timestamp: Optional[str] = None
    message: Optional[str] = None