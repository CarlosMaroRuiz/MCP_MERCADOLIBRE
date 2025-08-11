from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastmcp import Context
from fastmcp.exceptions import ToolError

from browser.browser import MercadoLibreBrowser


class UtilityTools:
    """Herramientas de utilidades generales"""
    
    def __init__(self, browser: MercadoLibreBrowser):
        self.browser = browser
    
    async def take_screenshot(
        self,
        filename: Optional[str] = None,
        full_page: bool = False,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Toma una captura de pantalla de la página actual.
        
        Args:
            filename: Nombre del archivo (opcional, se genera automáticamente si no se especifica)
            full_page: Si capturar toda la página o solo la parte visible
            ctx: Contexto de FastMCP
        
        Returns:
            Información sobre la captura tomada
        """
        if ctx:
            await ctx.info("Tomando captura de pantalla")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ml_screenshot_{timestamp}.png"
            
            # Asegurar que termine en .png
            if not filename.endswith('.png'):
                filename += '.png'
            
            screenshot_path = Path(filename)
            
            await self.browser.page.screenshot(
                path=screenshot_path,
                full_page=full_page
            )
            
            result = {
                'success': True,
                'filename': str(screenshot_path),
                'full_page': full_page,
                'page_url': self.browser.page.url,
                'page_title': await self.browser.page.title(),
                'timestamp': datetime.now().isoformat()
            }
            
            if ctx:
                await ctx.info(f"Captura guardada: {filename}")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error tomando captura: {str(e)}")
            raise ToolError(f"Error tomando captura de pantalla: {str(e)}")
    
    async def wait_for_element(
        self,
        selector: str,
        timeout: int = 5000,
        state: str = "visible",
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Espera a que aparezca un elemento específico.
        
        Args:
            selector: Selector CSS del elemento a esperar
            timeout: Tiempo máximo de espera en milisegundos
            state: Estado a esperar ("visible", "attached", "detached", "hidden")
            ctx: Contexto de FastMCP
        
        Returns:
            Resultado de la espera
        """
        if ctx:
            await ctx.info(f"Esperando elemento: {selector}")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            start_time = datetime.now()
            
            await self.browser.page.wait_for_selector(
                selector,
                timeout=timeout,
                state=state
            )
            
            end_time = datetime.now()
            wait_duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'selector': selector,
                'state': state,
                'wait_duration_seconds': wait_duration,
                'timeout_ms': timeout,
                'timestamp': datetime.now().isoformat()
            }
            
            if ctx:
                await ctx.info(f"Elemento encontrado en {wait_duration:.2f} segundos")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Elemento no encontrado: {str(e)}")
            raise ToolError(f"Elemento {selector} no encontrado: {str(e)}")