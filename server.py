# -*- coding: utf-8 -*-
"""
Servidor FastMCP actualizado con sistema de aprendizaje de errores
"""

import asyncio
import atexit
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastmcp import FastMCP, Context

# Importaciones existentes
from browser.browser import MercadoLibreBrowser
from browser.config import BrowserConfig
from tools.navigation import NavigationTools
from tools.extraction import ExtractionTools
from tools.selectors import SelectorTools
from tools.products import ProductTools
from tools.utilities import UtilityTools

# Nuevas importaciones para el sistema de errores
from tools.error_manager import CommonErrorManager
from tools.error_tools import ErrorLearningTools
from tools.error_wrapper import capture_tool_errors, EnhancedErrorCapture

# Crear directorio de datos si no existe
Path("data").mkdir(exist_ok=True)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MercadoLibreMCPServer:
    """Servidor MCP mejorado con aprendizaje de errores"""
    
    def __init__(self):
        # Inicializar sistema de errores
        self.error_manager = CommonErrorManager()
        self.enhanced_error_capture = EnhancedErrorCapture(self.error_manager)
        
        # Inicializar componentes
        self.browser = MercadoLibreBrowser(BrowserConfig())
        
        # Inicializar herramientas normales (el decorador se aplica en las funciones MCP)
        self.navigation_tools = NavigationTools(self.browser)
        self.extraction_tools = ExtractionTools(self.browser)
        self.selector_tools = SelectorTools(self.browser)
        self.product_tools = ProductTools(self.browser)
        self.utility_tools = UtilityTools(self.browser)
        
        # Inicializar herramientas de errores
        self.error_tools = ErrorLearningTools(self.error_manager)
        
        # Crear servidor FastMCP
        self.mcp = FastMCP(
            name="MercadoLibreMX-Enhanced",
            instructions="""
            Servidor MCP especializado para MercadoLibre México con sistema de aprendizaje de errores.
            
            🚀 NUEVAS CAPACIDADES DE APRENDIZAJE:
            - Sistema automático de captura y análisis de errores
            - Consejos de prevención basados en errores pasados
            - Estadísticas y patrones de errores comunes
            - Búsqueda de errores similares con soluciones
            - Insights de aprendizaje para mejora continua
            
            💡 RECOMENDACIÓN: Usa get_prevention_advice antes de ejecutar herramientas críticas
            
            Capacidades principales:
            - Navegación específica a mercadolibre.com.mx
            - Extracción de HTML para análisis
            - Descubrimiento y prueba de selectores CSS
            - Extracción de datos de productos
            - Navegación por páginas de resultados
            - Herramientas de debugging y análisis
            
            El sistema aprende automáticamente de cada error para mejorar futuras ejecuciones.
            """
        )
        
        # Registrar herramientas
        self._register_enhanced_tools()
        
        # Limpieza automática de errores antiguos al inicio
        self.error_manager.clear_old_errors(days=30)
        
        # Configurar cleanup
        atexit.register(self.cleanup)
    
    def _register_enhanced_tools(self):
        """Registra todas las herramientas con captura automática de errores"""
        
        # === HERRAMIENTAS DE APRENDIZAJE DE ERRORES (NUEVAS) ===
        
        @self.mcp.tool
        async def get_prevention_advice(
            tool_name: str,
            context_info: Optional[Dict[str, Any]] = None,
            user_query: Optional[str] = None,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            🛡️ Obtiene consejos de prevención antes de usar una herramienta.
            
            RECOMENDADO: Úsalo antes de ejecutar herramientas críticas para evitar errores conocidos.
            
            Args:
                tool_name: Nombre de la herramienta que vas a usar
                context_info: Información del contexto actual (opcional)
                user_query: Query del usuario (opcional)
            """
            return await self.error_tools.get_prevention_advice(
                tool_name, context_info, user_query, ctx
            )
        
        @self.mcp.tool
        async def get_error_statistics(ctx: Context = None) -> Dict[str, Any]:
            """
            📊 Obtiene estadísticas detalladas de errores comunes.
            
            Útil para entender qué errores son más frecuentes y cómo mejorar.
            """
            return await self.error_tools.get_error_statistics(ctx)
        
        @self.mcp.tool
        async def search_similar_errors(
            error_description: str,
            tool_name: Optional[str] = None,
            limit: int = 5,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            🔍 Busca errores similares en el historial con sus soluciones.
            
            Args:
                error_description: Descripción del error que quieres buscar
                tool_name: Filtrar por herramienta específica (opcional)
                limit: Número máximo de resultados
            """
            return await self.error_tools.search_similar_errors(
                error_description, tool_name, limit, ctx
            )
        
        @self.mcp.tool
        async def get_learning_insights(ctx: Context = None) -> Dict[str, Any]:
            """
            🧠 Obtiene insights y patrones de aprendizaje del historial de errores.
            
            Identifica tendencias, herramientas problemáticas y oportunidades de mejora.
            """
            return await self.error_tools.get_learning_insights(ctx)
        
        @self.mcp.tool
        async def export_error_data(
            format_type: str = "summary",
            include_statistics: bool = True,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            📤 Exporta datos de errores para análisis externo.
            
            Args:
                format_type: "json" para datos completos, "summary" para resumen
                include_statistics: Si incluir estadísticas
            """
            return await self.error_tools.export_error_data(
                format_type, include_statistics, ctx
            )
        
        # === HERRAMIENTAS DE NAVEGACIÓN (MEJORADAS) ===
        
        @self.mcp.tool
        @capture_tool_errors("navigate_to_page", self.error_manager)
        async def navigate_to_page(url: str, ctx: Context = None) -> Dict[str, Any]:
            """
            🌐 Navega a una página específica de MercadoLibre México.
            
            ⚠️ CON APRENDIZAJE DE ERRORES: Esta herramienta ahora aprende automáticamente
            de errores pasados y proporciona consejos preventivos.
            """
            return await self.navigation_tools.navigate_to_page(url, ctx)
        
        @self.mcp.tool
        @capture_tool_errors("go_to_home", self.error_manager)
        async def go_to_home(ctx: Context = None) -> Dict[str, Any]:
            """🏠 Navega a la página principal de MercadoLibre México."""
            return await self.navigation_tools.go_to_home(ctx)
        
        @self.mcp.tool
        @capture_tool_errors("search_products", self.error_manager)
        async def search_products(query: str, ctx: Context = None) -> Dict[str, Any]:
            """
            🔍 Busca productos en MercadoLibre México.
            
            ⚠️ TIP: Si falla frecuentemente, revisa las estadísticas de errores para este tool.
            """
            return await self.navigation_tools.search_products(query, ctx)
        
        @self.mcp.tool
        async def get_current_page_info(ctx: Context = None) -> Dict[str, Any]:
            """📄 Obtiene información sobre la página actual."""
            return await self.navigation_tools.get_current_page_info(ctx)
        
        @self.mcp.tool
        @capture_tool_errors("navigate_pagination", self.error_manager)
        async def navigate_pagination(direction: str = "next", ctx: Context = None) -> Dict[str, Any]:
            """⏭️ Navega por las páginas de resultados."""
            return await self.navigation_tools.navigate_pagination(direction, ctx)
        
        # === HERRAMIENTAS DE EXTRACCIÓN (MEJORADAS) ===
        
        @self.mcp.tool
        @capture_tool_errors("extract_page_html", self.error_manager)
        async def extract_page_html(
            selector: Optional[str] = None,
            max_length: int = 50000,
            pretty_format: bool = False,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """📜 Extrae HTML de la página actual o de un elemento específico."""
            return await self.extraction_tools.extract_page_html(
                selector, max_length, pretty_format, ctx
            )
        
        @self.mcp.tool
        @capture_tool_errors("extract_text_content", self.error_manager)
        async def extract_text_content(
            selector: str,
            all_matches: bool = False,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """📝 Extrae contenido de texto de elementos específicos."""
            return await self.extraction_tools.extract_text_content(
                selector, all_matches, ctx
            )
        
        # === HERRAMIENTAS DE SELECTORES (MEJORADAS) ===
        
        @self.mcp.tool
        @capture_tool_errors("discover_selectors", self.error_manager)
        async def discover_selectors(
            element_type: str = "products",
            ctx: Context = None
        ) -> Dict[str, Any]:
            """🔍 Descubre selectores CSS útiles en la página actual."""
            return await self.selector_tools.discover_selectors(element_type, ctx)
        
        @self.mcp.tool
        @capture_tool_errors("test_selector", self.error_manager)
        async def test_selector(
            selector: str,
            extract_text: bool = True,
            check_visibility: bool = True,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """🧪 Prueba un selector CSS específico para evaluar su utilidad."""
            return await self.selector_tools.test_selector(
                selector, extract_text, check_visibility, ctx
            )
        
        # === HERRAMIENTAS DE PRODUCTOS (MEJORADAS) ===
        
        @self.mcp.tool
        @capture_tool_errors("extract_products", self.error_manager)
        async def extract_products(
            limit: int = 20,
            custom_selectors: Optional[Dict[str, str]] = None,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            🛍️ Extrae datos de productos de la página actual.
            
            ⚠️ RECOMENDACIÓN: Usa get_prevention_advice("extract_products") primero
            si has tenido problemas anteriormente con esta herramienta.
            """
            return await self.product_tools.extract_products(
                limit, custom_selectors, ctx
            )
        
        # === HERRAMIENTAS DE UTILIDADES (MEJORADAS) ===
        
        @self.mcp.tool
        @capture_tool_errors("take_screenshot", self.error_manager)
        async def take_screenshot(
            filename: Optional[str] = None,
            full_page: bool = False,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """📸 Toma una captura de pantalla de la página actual."""
            return await self.utility_tools.take_screenshot(filename, full_page, ctx)
        
        @self.mcp.tool
        @capture_tool_errors("wait_for_element", self.error_manager)
        async def wait_for_element(
            selector: str,
            timeout: int = 5000,
            state: str = "visible",
            ctx: Context = None
        ) -> Dict[str, Any]:
            """⏳ Espera a que aparezca un elemento específico."""
            return await self.utility_tools.wait_for_element(
                selector, timeout, state, ctx
            )
        
        # === HERRAMIENTA DE FLUJO INTELIGENTE (NUEVA) ===
        
        @self.mcp.tool
        async def smart_search_and_extract(
            search_query: str,
            max_products: int = 20,
            auto_prevent_errors: bool = True,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """
            🤖 Flujo inteligente: busca productos y extrae datos con prevención automática de errores.
            
            Esta herramienta combina búsqueda y extracción con aprendizaje automático de errores.
            
            Args:
                search_query: Término de búsqueda
                max_products: Máximo número de productos a extraer
                auto_prevent_errors: Si aplicar consejos de prevención automáticamente
            """
            if ctx:
                await ctx.info(f"🚀 Iniciando búsqueda inteligente: '{search_query}'")
            
            results = {
                'search_query': search_query,
                'auto_prevention_used': auto_prevent_errors,
                'steps_completed': [],
                'errors_prevented': [],
                'final_results': None
            }
            
            try:
                # Paso 1: Obtener consejos preventivos si está habilitado
                if auto_prevent_errors and ctx:
                    await ctx.info("🛡️ Obteniendo consejos de prevención...")
                    
                    search_advice = await self.error_tools.get_prevention_advice(
                        "search_products", {'query': search_query}, search_query, ctx
                    )
                    extract_advice = await self.error_tools.get_prevention_advice(
                        "extract_products", {'max_products': max_products}, search_query, ctx
                    )
                    
                    if search_advice['recommendations'] or extract_advice['recommendations']:
                        total_recommendations = len(search_advice['recommendations']) + len(extract_advice['recommendations'])
                        await ctx.warning(f"⚠️ {total_recommendations} consejos de prevención aplicados")
                        results['errors_prevented'] = [
                            f"Búsqueda: {len(search_advice['recommendations'])} consejos",
                            f"Extracción: {len(extract_advice['recommendations'])} consejos"
                        ]
                
                # Paso 2: Ir a la página principal
                await ctx.info("🏠 Navegando a MercadoLibre...")
                home_result = await self.navigation_tools.go_to_home(ctx)
                results['steps_completed'].append("Navegación a home")
                
                # Paso 3: Realizar búsqueda
                await ctx.info(f"🔍 Buscando: {search_query}")
                search_result = await self.navigation_tools.search_products(search_query, ctx)
                results['steps_completed'].append("Búsqueda de productos")
                
                # Paso 4: Extraer productos
                await ctx.info(f"📦 Extrayendo hasta {max_products} productos...")
                extraction_result = await self.product_tools.extract_products(max_products, None, ctx)
                results['steps_completed'].append("Extracción de productos")
                
                # Compilar resultados finales
                results['final_results'] = {
                    'search_url': search_result.get('results_url'),
                    'products_found': extraction_result.get('extraction_info', {}).get('products_found', 0),
                    'products_extracted': len(extraction_result.get('products', [])),
                    'price_statistics': extraction_result.get('price_statistics'),
                    'products': extraction_result.get('products', [])
                }
                
                if ctx:
                    products_count = results['final_results']['products_extracted']
                    await ctx.info(f"✅ Flujo completado: {products_count} productos extraídos")
                
                return results
                
            except Exception as e:
                # Capturar error del flujo completo
                error_id = self.error_manager.capture_error(
                    error=e,
                    tool_name="smart_search_and_extract",
                    context_info={'search_query': search_query, 'max_products': max_products},
                    user_query=search_query
                )
                
                if ctx:
                    await ctx.error(f"❌ Error en flujo inteligente: {error_id}")
                
                results['error'] = {
                    'error_id': error_id,
                    'message': str(e),
                    'failed_at_step': len(results['steps_completed'])
                }
                
                return results
    
    def cleanup(self):
        """Limpia recursos al cerrar"""
        try:
            if self.browser.browser:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.browser.close())
                loop.close()
        except Exception as e:
            logger.error(f"Error durante cleanup: {e}")
    
    def run(self, transport: str = "stdio", **kwargs):
        """Ejecuta el servidor MCP mejorado"""
        logger.info("🚀 Iniciando servidor MCP con sistema de aprendizaje de errores")
        logger.info(f"📊 Errores conocidos en base de datos: {len(self.error_manager.error_patterns)}")
        
        self.mcp.run(transport=transport, **kwargs)


# Función de conveniencia para crear y ejecutar el servidor
def create_server() -> MercadoLibreMCPServer:
    """Crea una nueva instancia del servidor MercadoLibre MCP mejorado"""
    return MercadoLibreMCPServer()


# Instancia global del servidor (para compatibilidad con el código original)
server_instance = create_server()
mcp = server_instance.mcp