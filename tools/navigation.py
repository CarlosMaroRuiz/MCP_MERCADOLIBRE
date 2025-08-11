# -*- coding: utf-8 -*-
"""
Herramientas de navegación para MercadoLibre México
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastmcp import Context
from fastmcp.exceptions import ToolError

# Importaciones absolutas
from browser.browser import MercadoLibreBrowser
from models.product import NavigationResult


class NavigationTools:
    """Herramientas para navegación en MercadoLibre"""
    
    def __init__(self, browser: MercadoLibreBrowser):
        self.browser = browser
    
    async def navigate_to_page(self, url: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
        """
        Navega a una página específica de MercadoLibre México.
        
        Args:
            url: URL completa de MercadoLibre México
            ctx: Contexto de FastMCP
        
        Returns:
            Información sobre el resultado de la navegación
        """
        if ctx:
            await ctx.info(f"Navegando a: {url}")
        
        try:
            success = await self.browser.navigate(url)
            
            if not success:
                raise ToolError("No se pudo navegar a la URL especificada")
            
            page_info = await self.browser.get_page_info()
            
            result = NavigationResult(
                success=True,
                requested_url=url,
                final_url=page_info.url,
                page_title=page_info.title,
                is_ml_mexico=page_info.is_ml_mexico,
                timestamp=datetime.now().isoformat()
            )
            
            if ctx:
                await ctx.info(f"Navegación exitosa a: {page_info.title or 'Página sin título'}")
            
            return result.__dict__
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error navegando: {str(e)}")
            raise ToolError(f"Error navegando a {url}: {str(e)}")
    
    async def go_to_home(self, ctx: Optional[Context] = None) -> Dict[str, Any]:
        """
        Navega a la página principal de MercadoLibre México.
        
        Args:
            ctx: Contexto de FastMCP
        
        Returns:
            Información sobre la navegación a la homepage
        """
        if ctx:
            await ctx.info("Navegando a la página principal de MercadoLibre México")
        
        return await self.navigate_to_page(self.browser.config.BASE_URL, ctx)
    
    async def search_products(self, query: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
        """
        Busca productos en MercadoLibre México.
        
        Args:
            query: Término de búsqueda
            ctx: Contexto de FastMCP
        
        Returns:
            Resultado de la búsqueda con URL de resultados
        """
        if ctx:
            await ctx.info(f"Buscando productos: '{query}'")
        
        try:
            # Ir a homepage si no estamos ya ahí
            if not self.browser.page or not self.browser.is_valid_ml_url(self.browser.current_url):
                if ctx:
                    await ctx.info("Navegando a MercadoLibre México...")
                
                success = await self.browser.navigate(self.browser.config.BASE_URL)
                if not success:
                    raise ToolError("No se pudo navegar a MercadoLibre México")
            
            # Realizar búsqueda
            search_success = await self.browser.search(query)
            
            if not search_success:
                raise ToolError("No se pudo encontrar la caja de búsqueda en la página")
            
            # Verificar si llegamos a página de resultados
            current_url = self.browser.page.url
            is_search_results = '/search' in current_url or 'q=' in current_url
            
            result = {
                'search_query': query,
                'success': True,
                'results_url': current_url,
                'page_title': await self.browser.page.title(),
                'is_search_results_page': is_search_results,
                'timestamp': datetime.now().isoformat()
            }
            
            if ctx:
                await ctx.info(f"Búsqueda completada: {result['results_url']}")
                if is_search_results:
                    await ctx.info("✓ Llegamos a la página de resultados")
                else:
                    await ctx.warning("⚠️ No estamos en página de resultados típica")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error en búsqueda: {str(e)}")
            raise ToolError(f"Error buscando '{query}': {str(e)}")
    
    async def get_current_page_info(self, ctx: Optional[Context] = None) -> Dict[str, Any]:
        """
        Obtiene información sobre la página actual.
        
        Args:
            ctx: Contexto de FastMCP
        
        Returns:
            Información detallada de la página actual
        """
        if ctx:
            await ctx.info("Obteniendo información de la página actual")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            page_info = await self.browser.get_page_info()
            result = page_info.__dict__
            
            if ctx:
                await ctx.info(f"Página actual: {result.get('page_type', 'unknown')} - {result.get('title', 'Sin título')}")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error obteniendo información: {str(e)}")
            raise ToolError(f"Error obteniendo información de página: {str(e)}")
    
    async def navigate_pagination(self, direction: str = "next", ctx: Optional[Context] = None) -> Dict[str, Any]:
        """
        Navega por las páginas de resultados.
        
        Args:
            direction: Dirección de navegación ("next" o "previous")
            ctx: Contexto de FastMCP
        
        Returns:
            Resultado de la navegación
        """
        if ctx:
            await ctx.info(f"Navegando a página {direction}")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            current_url = self.browser.page.url
            success = await self.browser.navigate_pagination(direction)
            
            result = {
                'direction': direction,
                'success': success,
                'previous_url': current_url,
                'current_url': self.browser.page.url,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                if ctx:
                    await ctx.info(f"Navegación exitosa a página {direction}")
            else:
                if ctx:
                    await ctx.warning("No se pudo navegar - posiblemente no hay más páginas")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error navegando: {str(e)}")
            raise ToolError(f"Error navegando a página {direction}: {str(e)}")