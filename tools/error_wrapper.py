# -*- coding: utf-8 -*-
"""
Decorador y wrapper para captura automática de errores
"""

import functools
import logging
from typing import Callable, Any, Dict, Optional
from fastmcp import Context

from tools.error_manager import CommonErrorManager


logger = logging.getLogger(__name__)


class ErrorCaptureMixin:
    """Mixin para captura automática de errores en herramientas"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_manager = CommonErrorManager()
    
    def capture_errors(self, tool_name: str):
        """
        Decorador para capturar errores automáticamente
        
        Args:
            tool_name: Nombre de la herramienta para identificación
        
        Returns:
            Decorador que captura errores
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                ctx = None
                user_query = None
                context_info = {}
                
                # Extraer contexto y información de los argumentos
                for arg in args:
                    if isinstance(arg, Context):
                        ctx = arg
                        break
                
                # Buscar contexto en kwargs
                if not ctx and 'ctx' in kwargs:
                    ctx = kwargs['ctx']
                
                # Extraer query del usuario si está disponible
                if 'query' in kwargs:
                    user_query = kwargs['query']
                elif 'user_query' in kwargs:
                    user_query = kwargs['user_query']
                
                # Obtener información del contexto actual
                try:
                    if hasattr(self, 'browser') and self.browser.page:
                        page_info = await self.browser.get_page_info()
                        context_info = {
                            'page_url': page_info.url,
                            'page_type': page_info.page_type,
                            'page_title': page_info.title,
                            'is_ml_mexico': page_info.is_ml_mexico
                        }
                except Exception:
                    # Si no se puede obtener info de página, continuar
                    pass
                
                try:
                    # Obtener consejos de prevención antes de ejecutar
                    if ctx:
                        try:
                            recommendations = self.error_manager.get_prevention_advice(
                                tool_name=tool_name,
                                context_info=context_info,
                                user_query=user_query
                            )
                            
                            # Mostrar advertencias preventivas si hay errores comunes conocidos
                            if recommendations:
                                await ctx.warning(f"⚠️ Se han detectado {len(recommendations)} errores comunes para '{tool_name}'")
                                for rec in recommendations[:2]:  # Mostrar top 2
                                    await ctx.info(f"💡 Consejo: {rec.description}")
                        except Exception as prevention_error:
                            logger.debug(f"Error obteniendo consejos de prevención: {prevention_error}")
                    
                    # Ejecutar la función original
                    result = await func(*args, **kwargs)
                    
                    # Si llegamos aquí, la función se ejecutó exitosamente
                    if ctx:
                        await ctx.debug(f"✅ {tool_name} ejecutado exitosamente")
                    
                    return result
                    
                except Exception as e:
                    # Capturar el error para aprendizaje futuro
                    try:
                        error_id = self.error_manager.capture_error(
                            error=e,
                            tool_name=tool_name,
                            context_info=context_info,
                            user_query=user_query
                        )
                        
                        if ctx:
                            await ctx.error(f"❌ Error capturado: {error_id}")
                            
                            # Buscar errores similares para sugerir soluciones
                            similar_errors = []
                            for pattern in list(self.error_manager.error_patterns.values())[:5]:
                                if pattern.tool_name == tool_name and pattern.solution:
                                    similar_errors.append(pattern)
                            
                            if similar_errors:
                                await ctx.info("🔍 Errores similares encontrados:")
                                for pattern in similar_errors[:2]:
                                    await ctx.info(f"💡 {pattern.solution}")
                                    if pattern.prevention_tips:
                                        for tip in pattern.prevention_tips[:1]:
                                            await ctx.info(f"   - {tip}")
                        
                    except Exception as capture_error:
                        logger.error(f"Error capturando error: {capture_error}")
                    
                    # Re-lanzar el error original
                    raise e
            
            return wrapper
        return decorator


# Versión standalone del decorador para usar sin mixin
def capture_tool_errors(tool_name: str, error_manager: Optional[CommonErrorManager] = None):
    """
    Decorador standalone para captura de errores
    
    Args:
        tool_name: Nombre de la herramienta
        error_manager: Instancia del gestor de errores (se crea una nueva si no se proporciona)
    
    Returns:
        Decorador que captura errores
    """
    if error_manager is None:
        error_manager = CommonErrorManager()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = None
            user_query = None
            context_info = {}
            
            # Buscar contexto en los argumentos
            for arg in list(args) + list(kwargs.values()):
                if isinstance(arg, Context):
                    ctx = arg
                    break
            
            # Extraer información relevante
            if 'query' in kwargs:
                user_query = kwargs['query']
            elif 'user_query' in kwargs:
                user_query = kwargs['user_query']
            elif len(args) > 0 and isinstance(args[0], str):
                user_query = args[0]  # Primer argumento string como query
            
            try:
                # Obtener consejos preventivos
                if ctx:
                    try:
                        recommendations = error_manager.get_prevention_advice(
                            tool_name=tool_name,
                            context_info=context_info,
                            user_query=user_query
                        )
                        
                        if recommendations:
                            await ctx.info(f"💡 {len(recommendations)} consejos de prevención disponibles para {tool_name}")
                    except Exception:
                        pass
                
                # Ejecutar función
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                # Capturar error
                try:
                    error_id = error_manager.capture_error(
                        error=e,
                        tool_name=tool_name,
                        context_info=context_info,
                        user_query=user_query
                    )
                    
                    if ctx:
                        await ctx.error(f"Error registrado para aprendizaje: {error_id}")
                        
                except Exception as capture_error:
                    logger.error(f"Error en captura: {capture_error}")
                
                # Re-lanzar error original
                raise e
        
        return wrapper
    return decorator


class EnhancedErrorCapture:
    """Captura mejorada de errores con análisis en tiempo real"""
    
    def __init__(self, error_manager: CommonErrorManager):
        self.error_manager = error_manager
    
    async def analyze_and_suggest(
        self, 
        error: Exception, 
        tool_name: str, 
        context_info: Dict[str, Any],
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Analiza un error y proporciona sugerencias inmediatas
        
        Args:
            error: Excepción ocurrida
            tool_name: Herramienta que falló
            context_info: Información del contexto
            ctx: Contexto de FastMCP
        
        Returns:
            Análisis y sugerencias
        """
        # Capturar el error
        error_id = self.error_manager.capture_error(
            error=error,
            tool_name=tool_name,
            context_info=context_info
        )
        
        # Buscar errores similares
        error_str = str(error)
        similar_errors = []
        
        for pattern in self.error_manager.error_patterns.values():
            if (pattern.tool_name == tool_name and 
                pattern.error_id != error_id and
                any(word in pattern.error_message.lower() for word in error_str.lower().split()[:3])):
                similar_errors.append(pattern)
        
        # Generar sugerencias
        suggestions = []
        if similar_errors:
            # Usar soluciones de errores similares
            for pattern in similar_errors[:3]:
                if pattern.solution:
                    suggestions.append({
                        'type': 'solution',
                        'text': pattern.solution,
                        'confidence': 0.8,
                        'based_on': f"Error similar ocurrido {pattern.frequency} veces"
                    })
                
                for tip in pattern.prevention_tips[:2]:
                    suggestions.append({
                        'type': 'prevention',
                        'text': tip,
                        'confidence': 0.7,
                        'based_on': 'Prevención de errores similares'
                    })
        
        # Sugerencias generales basadas en el tipo de error
        if 'timeout' in error_str.lower():
            suggestions.append({
                'type': 'immediate_action',
                'text': 'Intentar aumentar el timeout o verificar la conexión',
                'confidence': 0.9,
                'based_on': 'Patrón de timeout detectado'
            })
        
        if 'not found' in error_str.lower() or 'no encontr' in error_str.lower():
            suggestions.append({
                'type': 'immediate_action',
                'text': 'Verificar que el elemento existe en la página actual',
                'confidence': 0.9,
                'based_on': 'Elemento no encontrado'
            })
        
        analysis = {
            'error_id': error_id,
            'similar_errors_found': len(similar_errors),
            'suggestions': suggestions,
            'confidence_level': 'high' if similar_errors else 'medium',
            'recommended_action': suggestions[0]['text'] if suggestions else 'Revisar documentación',
            'timestamp': error_id  # El ID ya incluye timestamp
        }
        
        # Reportar al contexto si está disponible
        if ctx:
            await ctx.info(f"🔍 Análisis del error {error_id[:8]}...")
            if suggestions:
                await ctx.info(f"💡 Sugerencia principal: {analysis['recommended_action']}")
                await ctx.info(f"🎯 Confianza: {analysis['confidence_level']}")
        
        return analysis