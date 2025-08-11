# -*- coding: utf-8 -*-
"""
Modelos de datos para productos de MercadoLibre México
"""

from dataclasses import dataclass
from typing import Optional, List, Any, Dict
from datetime import datetime


@dataclass
class ProductData:
    """Estructura de datos de producto de MercadoLibre México"""
    title: str
    price: Optional[str] = None
    original_price: Optional[str] = None
    discount: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    seller: Optional[str] = None
    rating: Optional[str] = None
    reviews: Optional[str] = None
    shipping: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None


@dataclass
class PriceStatistics:
    """Estadísticas de precios de productos"""
    total_products_with_price: int
    average_price_mxn: float
    min_price_mxn: float
    max_price_mxn: float
    products_with_discount: int


@dataclass
class ExtractionResult:
    """Resultado de extracción de productos"""
    extraction_info: Dict[str, Any]
    price_statistics: PriceStatistics
    products: List[Dict[str, Any]]
    errors: Optional[List[Dict[str, Any]]] = None


@dataclass
class NavigationResult:
    """Resultado de operaciones de navegación"""
    success: bool
    requested_url: Optional[str] = None
    final_url: Optional[str] = None
    page_title: Optional[str] = None
    is_ml_mexico: bool = False
    timestamp: Optional[str] = None
    message: Optional[str] = None


@dataclass
class PageInfo:
    """Información básica de una página"""
    url: str
    title: str
    is_ml_mexico: bool
    page_type: Optional[str] = None
    product_cards_found: int = 0
    timestamp: Optional[str] = None