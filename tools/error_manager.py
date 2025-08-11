# -*- coding: utf-8 -*-
"""
Sistema de gestión de errores comunes
"""

import json
import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from models.errors import ErrorPattern, ErrorCategory, ErrorSeverity, ErrorStatistics, ErrorRecommendation


logger = logging.getLogger(__name__)


class CommonErrorManager:
    """Gestor de errores comunes para aprendizaje automático"""
    
    def __init__(self, storage_path: str = "data/common_errors.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.load_errors()
    
    def capture_error(
        self,
        error: Exception,
        tool_name: str,
        context_info: Dict[str, Any],
        user_query: Optional[str] = None
    ) -> str:
        """
        Captura y categoriza un error para aprendizaje futuro
        
        Args:
            error: Excepción capturada
            tool_name: Nombre de la herramienta que generó el error
            context_info: Información del contexto (URL, página, etc.)
            user_query: Query del usuario que causó el error
        
        Returns:
            ID único del patrón de error
        """
        try:
            # Generar ID único basado en el error y contexto
            error_signature = self._generate_error_signature(error, tool_name, context_info)
            
            # Categorizar error
            category = self._categorize_error(error, tool_name)
            severity = self._determine_severity(error, category)
            
            # Generar solución y consejos
            solution, tips = self._generate_solution_and_tips(error, tool_name, category)
            
            current_time = datetime.now().isoformat()
            
            if error_signature in self.error_patterns:
                # Error existente - actualizar frecuencia
                pattern = self.error_patterns[error_signature]
                pattern.frequency += 1
                pattern.last_seen = current_time
                logger.info(f"Error conocido actualizado: {error_signature} (frecuencia: {pattern.frequency})")
            else:
                # Nuevo error - crear patrón
                pattern = ErrorPattern(
                    error_id=error_signature,
                    category=category,
                    severity=severity,
                    error_message=str(error),
                    original_error=type(error).__name__,
                    context_info=context_info,
                    solution=solution,
                    prevention_tips=tips,
                    tool_name=tool_name,
                    page_type=context_info.get('page_type'),
                    query_context=user_query
                )
                self.error_patterns[error_signature] = pattern
                logger.info(f"Nuevo error capturado: {error_signature}")
            
            # Guardar cambios
            self.save_errors()
            
            return error_signature
            
        except Exception as e:
            logger.error(f"Error capturando error: {e}")
            return "unknown_error"
    
    def get_prevention_advice(
        self,
        tool_name: str,
        context_info: Dict[str, Any],
        user_query: Optional[str] = None
    ) -> List[ErrorRecommendation]:
        """
        Obtiene consejos de prevención basados en errores comunes
        
        Args:
            tool_name: Herramienta que se va a usar
            context_info: Contexto actual
            user_query: Query del usuario
        
        Returns:
            Lista de recomendaciones de prevención
        """
        recommendations = []
        
        # Filtrar errores relevantes por herramienta
        relevant_errors = [
            pattern for pattern in self.error_patterns.values()
            if pattern.tool_name == tool_name and pattern.frequency > 1
        ]
        
        # Ordenar por frecuencia y severidad
        relevant_errors.sort(key=lambda x: (x.frequency, x.severity.value), reverse=True)
        
        # Generar recomendaciones basadas en los errores más comunes
        for i, error_pattern in enumerate(relevant_errors[:5]):  # Top 5
            recommendation = ErrorRecommendation(
                recommendation_id=f"rec_{error_pattern.error_id}",
                title=f"Evitar: {error_pattern.error_message}",
                description=f"Este error ha ocurrido {error_pattern.frequency} veces. {error_pattern.solution or 'Revisar el contexto antes de proceder.'}",
                related_errors=[error_pattern.error_id],
                prevention_steps=error_pattern.prevention_tips,
                applicable_contexts=[error_pattern.page_type or "cualquier página"],
                priority=5 - i  # Mayor prioridad para errores más frecuentes
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def get_error_statistics(self) -> ErrorStatistics:
        """Obtiene estadísticas de errores comunes"""
        if not self.error_patterns:
            return ErrorStatistics(
                total_errors=0,
                errors_by_category={},
                errors_by_severity={},
                most_common_errors=[],
                recent_errors=[],
                learning_suggestions=["No hay errores registrados aún."]
            )
        
        patterns = list(self.error_patterns.values())
        
        # Estadísticas por categoría
        errors_by_category = {}
        for pattern in patterns:
            category = pattern.category.value
            errors_by_category[category] = errors_by_category.get(category, 0) + pattern.frequency
        
        # Estadísticas por severidad
        errors_by_severity = {}
        for pattern in patterns:
            severity = pattern.severity.value
            errors_by_severity[severity] = errors_by_severity.get(severity, 0) + pattern.frequency
        
        # Errores más comunes
        most_common = sorted(patterns, key=lambda x: x.frequency, reverse=True)[:10]
        most_common_errors = [
            {
                'error_id': p.error_id,
                'message': p.error_message,
                'frequency': p.frequency,
                'category': p.category.value,
                'tool': p.tool_name
            }
            for p in most_common
        ]
        
        # Errores recientes (últimos 7 días)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent = [p for p in patterns if p.last_seen >= week_ago]
        recent_errors = [
            {
                'error_id': p.error_id,
                'message': p.error_message,
                'last_seen': p.last_seen,
                'tool': p.tool_name
            }
            for p in sorted(recent, key=lambda x: x.last_seen, reverse=True)[:10]
        ]
        
        # Sugerencias de aprendizaje
        learning_suggestions = self._generate_learning_suggestions(patterns)
        
        return ErrorStatistics(
            total_errors=len(patterns),
            errors_by_category=errors_by_category,
            errors_by_severity=errors_by_severity,
            most_common_errors=most_common_errors,
            recent_errors=recent_errors,
            learning_suggestions=learning_suggestions
        )
    
    def _generate_error_signature(self, error: Exception, tool_name: str, context: Dict[str, Any]) -> str:
        """Genera un ID único para el error"""
        signature_data = f"{type(error).__name__}:{str(error)[:100]}:{tool_name}:{context.get('page_type', 'unknown')}"
        return hashlib.md5(signature_data.encode()).hexdigest()[:12]
    
    def _categorize_error(self, error: Exception, tool_name: str) -> ErrorCategory:
        """Categoriza automáticamente el error"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Patrones de categorización
        if any(word in error_str for word in ['navigate', 'navegar', 'url', 'página']):
            return ErrorCategory.NAVIGATION
        elif any(word in error_str for word in ['selector', 'query_selector', 'elemento']):
            return ErrorCategory.SELECTOR
        elif any(word in error_str for word in ['extract', 'extracción', 'datos']):
            return ErrorCategory.EXTRACTION
        elif any(word in error_str for word in ['search', 'búsqueda', 'buscar']):
            return ErrorCategory.SEARCH
        elif any(word in error_str for word in ['pagination', 'paginación', 'siguiente', 'anterior']):
            return ErrorCategory.PAGINATION
        elif any(word in error_str for word in ['browser', 'playwright', 'chromium']):
            return ErrorCategory.BROWSER
        else:
            return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determina la severidad del error"""
        error_str = str(error).lower()
        
        # Errores críticos
        if any(word in error_str for word in ['crash', 'fatal', 'browser closed']):
            return ErrorSeverity.CRITICAL
        
        # Errores altos
        if any(word in error_str for word in ['timeout', 'connection', 'network']):
            return ErrorSeverity.HIGH
        
        # Errores de navegación son generalmente importantes
        if category == ErrorCategory.NAVIGATION:
            return ErrorSeverity.HIGH
        
        # Errores de selectores pueden ser medios o bajos
        if category == ErrorCategory.SELECTOR:
            if 'not found' in error_str or 'no encontr' in error_str:
                return ErrorSeverity.MEDIUM
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _generate_solution_and_tips(
        self, 
        error: Exception, 
        tool_name: str, 
        category: ErrorCategory
    ) -> tuple[Optional[str], List[str]]:
        """Genera solución y consejos de prevención"""
        error_str = str(error).lower()
        
        # Soluciones específicas por tipo de error
        solutions = {
            ErrorCategory.NAVIGATION: "Verificar que la URL sea de MercadoLibre México y esté accesible.",
            ErrorCategory.SELECTOR: "Usar selectores más específicos o probar selectores alternativos.",
            ErrorCategory.EXTRACTION: "Asegurar que la página esté completamente cargada antes de extraer.",
            ErrorCategory.SEARCH: "Verificar que esté en la página principal antes de buscar.",
            ErrorCategory.PAGINATION: "Confirmar que existen más páginas antes de navegar.",
            ErrorCategory.BROWSER: "Reinicializar el navegador si es necesario."
        }
        
        # Consejos específicos
        tips_by_category = {
            ErrorCategory.NAVIGATION: [
                "Siempre verificar que la URL contenga 'mercadolibre.com.mx'",
                "Esperar a que la página cargue completamente antes de continuar",
                "Usar get_current_page_info() para verificar el estado de la página"
            ],
            ErrorCategory.SELECTOR: [
                "Usar discover_selectors() para encontrar selectores válidos",
                "Probar test_selector() antes de usar un selector en extracción",
                "Verificar que los elementos sean visibles con check_visibility=True"
            ],
            ErrorCategory.EXTRACTION: [
                "Confirmar que hay productos en la página antes de extraer",
                "Usar límites razonables en extract_products()",
                "Verificar el page_type antes de extraer datos"
            ],
            ErrorCategory.SEARCH: [
                "Navegar a la página principal antes de buscar",
                "Usar términos de búsqueda claros y en español",
                "Verificar que aparezcan resultados después de buscar"
            ],
            ErrorCategory.PAGINATION: [
                "Verificar que haya enlaces de navegación disponibles",
                "Comprobar el número de página actual antes de navegar",
                "Usar get_current_page_info() para verificar el contexto"
            ]
        }
        
        solution = solutions.get(category)
        tips = tips_by_category.get(category, ["Revisar la documentación de la herramienta."])
        
        # Consejos específicos basados en el error
        if 'timeout' in error_str:
            tips.append("Aumentar el timeout o verificar la conexión de red")
        if 'not found' in error_str or 'no encontr' in error_str:
            tips.append("Verificar que el elemento exista en la página actual")
        
        return solution, tips
    
    def _generate_learning_suggestions(self, patterns: List[ErrorPattern]) -> List[str]:
        """Genera sugerencias de aprendizaje basadas en patrones"""
        suggestions = []
        
        if not patterns:
            return ["Aún no hay suficientes datos para generar sugerencias."]
        
        # Análisis de frecuencia
        high_frequency_errors = [p for p in patterns if p.frequency >= 3]
        if high_frequency_errors:
            suggestions.append(f"Se han identificado {len(high_frequency_errors)} errores frecuentes. Considera revisar la lógica de estas operaciones.")
        
        # Análisis por categoría
        category_counts = {}
        for pattern in patterns:
            cat = pattern.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        if category_counts:
            most_common_category = max(category_counts.keys(), key=lambda x: category_counts[x])
            suggestions.append(f"La categoría más problemática es '{most_common_category}'. Considera mejorar el manejo en esta área.")
        
        # Análisis temporal
        recent_patterns = [p for p in patterns if p.last_seen >= (datetime.now() - timedelta(days=3)).isoformat()]
        if len(recent_patterns) > len(patterns) * 0.5:
            suggestions.append("Muchos errores son recientes. Puede haber cambios en el sitio web o en el código.")
        
        return suggestions
    
    def load_errors(self):
        """Carga errores desde el archivo JSON"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for error_id, error_data in data.items():
                    # Convertir strings de enum de vuelta a enums
                    error_data['category'] = ErrorCategory(error_data['category'])
                    error_data['severity'] = ErrorSeverity(error_data['severity'])
                    
                    self.error_patterns[error_id] = ErrorPattern(**error_data)
                
                logger.info(f"Cargados {len(self.error_patterns)} patrones de error desde {self.storage_path}")
        except Exception as e:
            logger.error(f"Error cargando patrones de error: {e}")
            self.error_patterns = {}
    
    def save_errors(self):
        """Guarda errores en el archivo JSON"""
        try:
            # Convertir a diccionario serializable
            data = {}
            for error_id, pattern in self.error_patterns.items():
                pattern_dict = asdict(pattern)
                # Convertir enums a strings
                pattern_dict['category'] = pattern.category.value
                pattern_dict['severity'] = pattern.severity.value
                data[error_id] = pattern_dict
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Guardados {len(self.error_patterns)} patrones de error en {self.storage_path}")
        except Exception as e:
            logger.error(f"Error guardando patrones de error: {e}")
    
    def clear_old_errors(self, days: int = 30):
        """Limpia errores antiguos que no han vuelto a ocurrir"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        old_errors = [
            error_id for error_id, pattern in self.error_patterns.items()
            if pattern.last_seen < cutoff_date and pattern.frequency == 1
        ]
        
        for error_id in old_errors:
            del self.error_patterns[error_id]
        
        if old_errors:
            self.save_errors()
            logger.info(f"Limpiados {len(old_errors)} errores antiguos")
    
    def export_learning_data(self) -> Dict[str, Any]:
        """Exporta datos de aprendizaje para análisis externo"""
        return {
            'total_patterns': len(self.error_patterns),
            'patterns': [asdict(pattern) for pattern in self.error_patterns.values()],
            'statistics': asdict(self.get_error_statistics()),
            'export_timestamp': datetime.now().isoformat()
        }