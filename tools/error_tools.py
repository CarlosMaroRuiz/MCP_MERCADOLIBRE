# -*- coding: utf-8 -*-
"""
Herramientas MCP para gestión de errores comunes
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from fastmcp import Context
from fastmcp.exceptions import ToolError
from dataclasses import asdict

from models.errors import ErrorRecommendation
from tools.error_manager import CommonErrorManager


class ErrorLearningTools:
    """Herramientas para aprendizaje y consulta de errores comunes"""
    
    def __init__(self, error_manager: CommonErrorManager):
        self.error_manager = error_manager
    
    async def get_prevention_advice(
        self,
        tool_name: str,
        context_info: Optional[Dict[str, Any]] = None,
        user_query: Optional[str] = None,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Obtiene consejos de prevención antes de ejecutar una herramienta.
        
        Args:
            tool_name: Nombre de la herramienta que se va a usar
            context_info: Información del contexto actual
            user_query: Query del usuario
            ctx: Contexto de FastMCP
        
        Returns:
            Consejos de prevención basados en errores comunes
        """
        if ctx:
            await ctx.info(f"Obteniendo consejos de prevención para: {tool_name}")
        
        try:
            context_info = context_info or {}
            recommendations = self.error_manager.get_prevention_advice(
                tool_name=tool_name,
                context_info=context_info,
                user_query=user_query
            )
            
            result = {
                'tool_name': tool_name,
                'total_recommendations': len(recommendations),
                'recommendations': [asdict(rec) for rec in recommendations],
                'context_analyzed': context_info,
                'timestamp': datetime.now().isoformat()
            }
            
            if recommendations:
                if ctx:
                    await ctx.info(f"Se encontraron {len(recommendations)} recomendaciones de prevención")
                    for i, rec in enumerate(recommendations[:3], 1):  # Mostrar top 3
                        await ctx.warning(f"⚠️ Consejo {i}: {rec.title}")
            else:
                if ctx:
                    await ctx.info("No se encontraron errores comunes para esta herramienta")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error obteniendo consejos: {str(e)}")
            raise ToolError(f"Error obteniendo consejos de prevención: {str(e)}")
    
    async def get_error_statistics(self, ctx: Optional[Context] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas detalladas de errores comunes.
        
        Args:
            ctx: Contexto de FastMCP
        
        Returns:
            Estadísticas completas de errores registrados
        """
        if ctx:
            await ctx.info("Obteniendo estadísticas de errores comunes")
        
        try:
            stats = self.error_manager.get_error_statistics()
            result = asdict(stats)
            
            if ctx:
                await ctx.info(f"📊 Total de errores únicos: {stats.total_errors}")
                if stats.most_common_errors:
                    await ctx.info(f"🔥 Error más común: {stats.most_common_errors[0]['message']} ({stats.most_common_errors[0]['frequency']} veces)")
                
                # Mostrar sugerencias de aprendizaje
                for suggestion in stats.learning_suggestions[:3]:
                    await ctx.info(f"💡 {suggestion}")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error obteniendo estadísticas: {str(e)}")
            raise ToolError(f"Error obteniendo estadísticas de errores: {str(e)}")
    
    async def search_similar_errors(
        self,
        error_description: str,
        tool_name: Optional[str] = None,
        limit: int = 5,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Busca errores similares en el historial.
        
        Args:
            error_description: Descripción del error a buscar
            tool_name: Filtrar por herramienta específica
            limit: Número máximo de resultados
            ctx: Contexto de FastMCP
        
        Returns:
            Errores similares encontrados con sus soluciones
        """
        if ctx:
            await ctx.info(f"Buscando errores similares a: '{error_description[:50]}...'")
        
        try:
            search_terms = error_description.lower().split()
            similar_errors = []
            
            for pattern in self.error_manager.error_patterns.values():
                if tool_name and pattern.tool_name != tool_name:
                    continue
                
                # Calcular similitud básica
                pattern_text = f"{pattern.error_message} {pattern.original_error}".lower()
                matches = sum(1 for term in search_terms if term in pattern_text)
                similarity = matches / len(search_terms) if search_terms else 0
                
                if similarity > 0.3:  # Umbral de similitud
                    similar_errors.append({
                        'error_id': pattern.error_id,
                        'similarity_score': similarity,
                        'error_message': pattern.error_message,
                        'frequency': pattern.frequency,
                        'category': pattern.category.value,
                        'severity': pattern.severity.value,
                        'solution': pattern.solution,
                        'prevention_tips': pattern.prevention_tips,
                        'tool_name': pattern.tool_name,
                        'last_seen': pattern.last_seen
                    })
            
            # Ordenar por similitud y frecuencia
            similar_errors.sort(key=lambda x: (x['similarity_score'], x['frequency']), reverse=True)
            similar_errors = similar_errors[:limit]
            
            result = {
                'search_query': error_description,
                'tool_filter': tool_name,
                'total_found': len(similar_errors),
                'similar_errors': similar_errors,
                'timestamp': datetime.now().isoformat()
            }
            
            if ctx:
                if similar_errors:
                    await ctx.info(f"Se encontraron {len(similar_errors)} errores similares")
                    best_match = similar_errors[0]
                    await ctx.info(f"🎯 Mejor coincidencia: {best_match['error_message']}")
                    if best_match['solution']:
                        await ctx.info(f"💡 Solución sugerida: {best_match['solution']}")
                else:
                    await ctx.info("No se encontraron errores similares en el historial")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error buscando errores similares: {str(e)}")
            raise ToolError(f"Error buscando errores similares: {str(e)}")
    
    async def get_learning_insights(self, ctx: Optional[Context] = None) -> Dict[str, Any]:
        """
        Obtiene insights y patrones de aprendizaje del historial de errores.
        
        Args:
            ctx: Contexto de FastMCP
        
        Returns:
            Insights y patrones identificados
        """
        if ctx:
            await ctx.info("Analizando patrones de aprendizaje")
        
        try:
            stats = self.error_manager.get_error_statistics()
            patterns = list(self.error_manager.error_patterns.values())
            
            # Análisis de patrones temporales
            recent_errors = [p for p in patterns if 
                           (datetime.now() - datetime.fromisoformat(p.last_seen.replace('Z', '+00:00').replace('+00:00', ''))).days <= 7]
            
            # Análisis de herramientas problemáticas
            tool_errors = {}
            for pattern in patterns:
                if pattern.tool_name:
                    tool_errors[pattern.tool_name] = tool_errors.get(pattern.tool_name, 0) + pattern.frequency
            
            # Top herramientas con más errores
            problematic_tools = sorted(tool_errors.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Análisis de evolución (errores que han mejorado vs empeorado)
            stable_errors = [p for p in patterns if p.frequency == 1]
            recurring_errors = [p for p in patterns if p.frequency > 3]
            
            insights = {
                'summary': {
                    'total_unique_errors': len(patterns),
                    'recent_errors_count': len(recent_errors),
                    'stable_errors': len(stable_errors),
                    'recurring_errors': len(recurring_errors)
                },
                'problematic_tools': [
                    {'tool_name': tool, 'error_frequency': freq} 
                    for tool, freq in problematic_tools
                ],
                'category_analysis': stats.errors_by_category,
                'severity_distribution': stats.errors_by_severity,
                'learning_recommendations': [
                    "Priorizar mejoras en las herramientas con más errores recurrentes",
                    "Revisar cambios recientes si hay picos en errores nuevos",
                    "Implementar validaciones adicionales para categorías problemáticas",
                    "Crear documentación específica para errores frecuentes"
                ],
                'success_indicators': [
                    f"{len(stable_errors)} errores han ocurrido solo una vez (buena resolución)",
                    f"{len(patterns) - len(recurring_errors)} errores no son recurrentes"
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            if ctx:
                await ctx.info(f"📈 Análisis completado: {len(patterns)} patrones analizados")
                await ctx.info(f"🔴 Errores recurrentes: {len(recurring_errors)}")
                await ctx.info(f"🟢 Errores estables: {len(stable_errors)}")
                
                if problematic_tools:
                    tool_name, freq = problematic_tools[0]
                    await ctx.warning(f"⚠️ Herramienta más problemática: {tool_name} ({freq} errores)")
            
            return insights
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error analizando patrones: {str(e)}")
            raise ToolError(f"Error obteniendo insights de aprendizaje: {str(e)}")
    
    async def export_error_data(
        self,
        format_type: str = "json",
        include_statistics: bool = True,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Exporta todos los datos de errores para análisis externo.
        
        Args:
            format_type: Formato de exportación ("json", "summary")
            include_statistics: Si incluir estadísticas en la exportación
            ctx: Contexto de FastMCP
        
        Returns:
            Datos exportados en el formato solicitado
        """
        if ctx:
            await ctx.info(f"Exportando datos de errores en formato {format_type}")
        
        try:
            export_data = self.error_manager.export_learning_data()
            
            if format_type == "summary":
                # Versión resumida para el modelo
                summary = {
                    'total_errors': export_data['total_patterns'],
                    'export_time': export_data['export_timestamp'],
                    'most_common_errors': export_data['statistics']['most_common_errors'][:10],
                    'learning_suggestions': export_data['statistics']['learning_suggestions'],
                    'category_breakdown': export_data['statistics']['errors_by_category'],
                    'prevention_guidelines': self._generate_prevention_guidelines()
                }
                result = summary
            else:
                result = export_data
            
            if ctx:
                await ctx.info(f"Exportación completada: {export_data['total_patterns']} patrones")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error exportando datos: {str(e)}")
            raise ToolError(f"Error exportando datos de errores: {str(e)}")
    
    def _generate_prevention_guidelines(self) -> Dict[str, List[str]]:
        """Genera guías de prevención generales"""
        return {
            'before_navigation': [
                "Verificar que la URL sea de MercadoLibre México",
                "Comprobar la conectividad de red",
                "Asegurar que el navegador esté inicializado"
            ],
            'before_extraction': [
                "Confirmar que la página está completamente cargada",
                "Verificar que hay elementos para extraer",
                "Usar selectores validados previamente"
            ],
            'before_search': [
                "Estar en la página principal de MercadoLibre",
                "Usar términos de búsqueda claros",
                "Verificar que la caja de búsqueda sea accesible"
            ],
            'general_best_practices': [
                "Usar timeouts apropiados",
                "Manejar errores graciosamente",
                "Validar el contexto antes de cada operación",
                "Reportar progreso en operaciones largas"
            ]
        }