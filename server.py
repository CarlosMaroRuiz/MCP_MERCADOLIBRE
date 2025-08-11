# -*- coding: utf-8 -*-
"""
Servidor FastMCP para MercadoLibre México
Configuración y registro de todas las herramientas
"""

import asyncio
import atexit
import logging
from typing import Dict, Any, Optional
from fastmcp import FastMCP, Context

# Importaciones absolutas (sin puntos)
from browser.browser import MercadoLibreBrowser
from browser.config import BrowserConfig
from tools.navigation import NavigationTools
from tools.extraction import ExtractionTools
from tools.selectors import SelectorTools
from tools.products import ProductTools
from tools.utilities import UtilityTools


# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MercadoLibreMCPServer:
    """Servidor MCP para MercadoLibre México"""
    
    def __init__(self):
        # Inicializar componentes
        self.browser = MercadoLibreBrowser(BrowserConfig())
        
        # Inicializar herramientas
        self.navigation_tools = NavigationTools(self.browser)
        self.extraction_tools = ExtractionTools(self.browser)
        self.selector_tools = SelectorTools(self.browser)
        self.product_tools = ProductTools(self.browser)
        self.utility_tools = UtilityTools(self.browser)
        
        # Crear servidor FastMCP
        self.mcp = FastMCP(
            name="MercadoLibreMX",
            instructions="""
            Servidor MCP especializado para MercadoLibre México.
            
            Capacidades:
            - Navegación específica a mercadolibre.com.mx
            - Extracción de HTML para análisis
            - Descubrimiento y prueba de selectores CSS
            - Extracción de datos de productos
            - Navegación por páginas de resultados
            - Herramientas de debugging y análisis
            
            Enfocado exclusivamente en el mercado mexicano con precios en MXN.
            """
        )
        
        
        # Registrar herramientas
        self._register_tools()
        
        # Configurar cleanup
        atexit.register(self.cleanup)
    
    def _register_tools(self):
        """Registra todas las herramientas con el servidor FastMCP"""
        
        # === HERRAMIENTAS DE NAVEGACIÓN ===
        
        @self.mcp.tool
        async def navigate_to_page(url: str, ctx: Context = None) -> Dict[str, Any]:
            """Navega a una página específica de MercadoLibre México."""
            return await self.navigation_tools.navigate_to_page(url, ctx)
        
        @self.mcp.tool
        async def go_to_home(ctx: Context = None) -> Dict[str, Any]:
            """Navega a la página principal de MercadoLibre México."""
            return await self.navigation_tools.go_to_home(ctx)
        
        @self.mcp.tool
        async def search_products(query: str, ctx: Context = None) -> Dict[str, Any]:
            """Busca productos en MercadoLibre México."""
            return await self.navigation_tools.search_products(query, ctx)
        
        @self.mcp.tool
        async def get_current_page_info(ctx: Context = None) -> Dict[str, Any]:
            """Obtiene información sobre la página actual."""
            return await self.navigation_tools.get_current_page_info(ctx)
        
        @self.mcp.tool
        async def navigate_pagination(direction: str = "next", ctx: Context = None) -> Dict[str, Any]:
            """Navega por las páginas de resultados."""
            return await self.navigation_tools.navigate_pagination(direction, ctx)
        
        # === HERRAMIENTAS DE EXTRACCIÓN ===
        
        @self.mcp.tool
        async def extract_page_html(
            selector: Optional[str] = None,
            max_length: int = 50000,
            pretty_format: bool = False,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """Extrae HTML de la página actual o de un elemento específico."""
            return await self.extraction_tools.extract_page_html(
                selector, max_length, pretty_format, ctx
            )
        
        @self.mcp.tool
        async def extract_text_content(
            selector: str,
            all_matches: bool = False,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """Extrae contenido de texto de elementos específicos."""
            return await self.extraction_tools.extract_text_content(
                selector, all_matches, ctx
            )
        
        # === HERRAMIENTAS DE SELECTORES ===
        
        @self.mcp.tool
        async def discover_selectors(
            element_type: str = "products",
            ctx: Context = None
        ) -> Dict[str, Any]:
            """Descubre selectores CSS útiles en la página actual."""
            return await self.selector_tools.discover_selectors(element_type, ctx)
        
        @self.mcp.tool
        async def test_selector(
            selector: str,
            extract_text: bool = True,
            check_visibility: bool = True,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """Prueba un selector CSS específico para evaluar su utilidad."""
            return await self.selector_tools.test_selector(
                selector, extract_text, check_visibility, ctx
            )
        
        # === HERRAMIENTAS DE PRODUCTOS ===
        
        @self.mcp.tool
        async def extract_products(
            limit: int = 20,
            custom_selectors: Optional[Dict[str, str]] = None,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """Extrae datos de productos de la página actual."""
            return await self.product_tools.extract_products(
                limit, custom_selectors, ctx
            )
        
        # === HERRAMIENTAS DE UTILIDADES ===
        
        @self.mcp.tool
        async def take_screenshot(
            filename: Optional[str] = None,
            full_page: bool = False,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """Toma una captura de pantalla de la página actual."""
            return await self.utility_tools.take_screenshot(filename, full_page, ctx)
        
        @self.mcp.tool
        async def wait_for_element(
            selector: str,
            timeout: int = 5000,
            state: str = "visible",
            ctx: Context = None
        ) -> Dict[str, Any]:
            """Espera a que aparezca un elemento específico."""
            return await self.utility_tools.wait_for_element(
                selector, timeout, state, ctx
            )
    
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
        """Ejecuta el servidor MCP"""
        self.mcp.run(transport=transport, **kwargs)


# Función de conveniencia para crear y ejecutar el servidor
def create_server() -> MercadoLibreMCPServer:
    """Crea una nueva instancia del servidor MercadoLibre MCP"""
    return MercadoLibreMCPServer()


# Instancia global del servidor (para compatibilidad con el código original)
server_instance = create_server()
mcp = server_instance.mcp