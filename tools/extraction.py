
from datetime import datetime
from typing import Dict, Any, Optional
from fastmcp import Context
from fastmcp.exceptions import ToolError

from browser.browser import MercadoLibreBrowser


class ExtractionTools:
    """Herramientas para extracción de HTML y contenido"""
    
    def __init__(self, browser: MercadoLibreBrowser):
        self.browser = browser
    
    async def extract_page_html(
        self, 
        selector: Optional[str] = None,
        max_length: int = 50000,
        pretty_format: bool = False,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Extrae HTML de la página actual o de un elemento específico.
        
        Args:
            selector: Selector CSS para extraer solo un elemento específico (opcional)
            max_length: Máximo número de caracteres de HTML a retornar
            pretty_format: Si formatear el HTML de manera legible
            ctx: Contexto de FastMCP
        
        Returns:
            HTML extraído con metadatos
        """
        if ctx:
            await ctx.info(f"Extrayendo HTML{f' del selector: {selector}' if selector else ' completo'}")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            # Extraer HTML
            if selector:
                try:
                    element = await self.browser.page.query_selector(selector)
                    if element:
                        html_content = await element.inner_html()
                        extraction_scope = f"elemento: {selector}"
                    else:
                        raise ToolError(f"No se encontró elemento con selector: {selector}")
                except Exception as e:
                    raise ToolError(f"Error extrayendo elemento {selector}: {str(e)}")
            else:
                html_content = await self.browser.page.content()
                extraction_scope = "página completa"
            
            # Procesar HTML
            original_length = len(html_content)
            truncated = False
            
            if len(html_content) > max_length:
                html_content = html_content[:max_length]
                truncated = True
            
            # Formatear si se solicita
            if pretty_format:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    html_content = soup.prettify()
                except ImportError:
                    # Si no está disponible BeautifulSoup, formato básico
                    html_content = html_content.replace('><', '>\n<')
            
            page_info = await self.browser.get_page_info()
            
            result = {
                'extraction_info': {
                    'scope': extraction_scope,
                    'selector_used': selector,
                    'original_length': original_length,
                    'extracted_length': len(html_content),
                    'truncated': truncated,
                    'pretty_formatted': pretty_format,
                    'timestamp': datetime.now().isoformat()
                },
                'page_info': page_info.__dict__,
                'html_content': html_content,
                'analysis_hints': {
                    'mercadolibre_patterns': [
                        'Buscar clases que contengan "ui-search" para productos',
                        'Buscar clases que contengan "andes-" para componentes de UI',
                        'Buscar elementos con precios ($, MXN)',
                        'Buscar enlaces con /p/ para productos individuales',
                        'Buscar clases "nav-" para navegación'
                    ],
                    'useful_selectors': [
                        '.ui-search-result (tarjetas de producto)',
                        '.ui-search-item__title (títulos)',
                        '.andes-money-amount (precios)',
                        '.ui-search-item__shipping (envío)',
                        '.andes-pagination (paginación)'
                    ]
                }
            }
            
            if ctx:
                await ctx.info(f"HTML extraído: {len(html_content)} caracteres de {original_length}")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error extrayendo HTML: {str(e)}")
            raise ToolError(f"Error extrayendo HTML: {str(e)}")
    
    async def extract_text_content(
        self,
        selector: str,
        all_matches: bool = False,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Extrae contenido de texto de elementos específicos.
        
        Args:
            selector: Selector CSS para encontrar elementos
            all_matches: Si extraer de todos los elementos encontrados o solo el primero
            ctx: Contexto de FastMCP
        
        Returns:
            Texto extraído de los elementos
        """
        if ctx:
            await ctx.info(f"Extrayendo texto con selector: {selector}")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            if all_matches:
                elements = await self.browser.page.query_selector_all(selector)
            else:
                element = await self.browser.page.query_selector(selector)
                elements = [element] if element else []
            
            if not elements:
                raise ToolError(f"No se encontraron elementos con selector: {selector}")
            
            extracted_texts = []
            for i, element in enumerate(elements):
                try:
                    text = await element.inner_text()
                    extracted_texts.append({
                        'index': i,
                        'text': text.strip(),
                        'length': len(text.strip())
                    })
                except Exception as e:
                    extracted_texts.append({
                        'index': i,
                        'error': str(e)
                    })
            
            result = {
                'selector': selector,
                'all_matches': all_matches,
                'elements_found': len(elements),
                'successful_extractions': len([t for t in extracted_texts if 'text' in t]),
                'extracted_texts': extracted_texts,
                'timestamp': datetime.now().isoformat()
            }
            
            if ctx:
                await ctx.info(f"Texto extraído de {result['successful_extractions']}/{len(elements)} elementos")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error extrayendo texto: {str(e)}")
            raise ToolError(f"Error extrayendo texto: {str(e)}")