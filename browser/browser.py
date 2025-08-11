# -*- coding: utf-8 -*-
"""
Navegador simplificado para MercadoLibre México
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from models.product import PageInfo
from .config import BrowserConfig


logger = logging.getLogger(__name__)


class MercadoLibreBrowser:
    """Navegador simplificado para MercadoLibre México"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_url = ""
        
    async def initialize(self):
        """Inicializar navegador"""
        if self.browser:
            return
            
        playwright = await async_playwright().__aenter__()
        
        self.browser = await playwright.chromium.launch(
            headless=self.config.HEADLESS,
            args=self.config.BROWSER_ARGS
        )
        
        self.context = await self.browser.new_context(
            viewport=self.config.VIEWPORT,
            user_agent=self.config.USER_AGENT,
            locale=self.config.LOCALE,
            timezone_id=self.config.TIMEZONE
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config.TIMEOUT)
        
    async def close(self):
        """Cerrar navegador"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
    
    async def navigate(self, url: str) -> bool:
        """Navegar a URL específica"""
        try:
            await self.initialize()
            
            # Validar que sea URL de MercadoLibre México
            if not self.is_valid_ml_url(url):
                raise ValueError(f"URL no es de MercadoLibre México: {url}")
            
            await self.page.goto(url, wait_until='networkidle', timeout=self.config.TIMEOUT)
            self.current_url = self.page.url
            await asyncio.sleep(2)  # Esperar carga completa
            return True
            
        except Exception as e:
            logger.error(f"Error navegando a {url}: {e}")
            return False
    
    def is_valid_ml_url(self, url: str) -> bool:
        """Validar que la URL sea de MercadoLibre México"""
        parsed = urlparse(url)
        return parsed.netloc in self.config.VALID_DOMAINS
    
    async def get_page_info(self) -> PageInfo:
        """Obtener información básica de la página actual"""
        if not self.page:
            return PageInfo(
                url="",
                title="",
                is_ml_mexico=False,
                timestamp=datetime.now().isoformat()
            )
            
        try:
            url = self.page.url
            title = await self.page.title()
            is_ml_mexico = self.is_valid_ml_url(url)
            
            # Detectar tipo de página
            page_type = self._detect_page_type(url)
            
            # Contar productos si es página de resultados
            product_cards_found = 0
            if page_type == 'search_results':
                try:
                    product_cards = await self.page.query_selector_all(
                        self.config.DEFAULT_SELECTORS['product_card']
                    )
                    product_cards_found = len(product_cards)
                except Exception:
                    pass
            
            return PageInfo(
                url=url,
                title=title,
                is_ml_mexico=is_ml_mexico,
                page_type=page_type,
                product_cards_found=product_cards_found,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo info de página: {e}")
            return PageInfo(
                url="",
                title="",
                is_ml_mexico=False,
                timestamp=datetime.now().isoformat()
            )
    
    def _detect_page_type(self, url: str) -> str:
        """Detectar el tipo de página actual"""
        if '/search' in url or 'q=' in url:
            return 'search_results'
        elif '/p/' in url or 'MLA' in url:
            return 'product_detail'
        elif url == self.config.BASE_URL or url == self.config.BASE_URL + '/':
            return 'homepage'
        else:
            return 'other'
    
    async def search(self, query: str) -> bool:
        """Realizar búsqueda en MercadoLibre"""
        try:
            # Buscar caja de búsqueda
            for selector in self.config.SEARCH_SELECTORS:
                try:
                    search_box = await self.page.query_selector(selector)
                    if search_box and await search_box.is_visible():
                        # Limpiar y escribir
                        await search_box.fill("")
                        await asyncio.sleep(0.5)
                        await search_box.fill(query)
                        await search_box.press('Enter')
                        
                        # Esperar resultados
                        await self.page.wait_for_load_state('networkidle')
                        await asyncio.sleep(2)
                        
                        self.current_url = self.page.url
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return False
    
    async def navigate_pagination(self, direction: str = "next") -> bool:
        """Navegar páginas de resultados"""
        try:
            current_url = self.page.url
            selectors = self.config.PAGINATION_SELECTORS.get(direction, [])
            
            for selector in selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible() and await element.is_enabled():
                        await element.click()
                        await self.page.wait_for_load_state('networkidle')
                        
                        # Verificar si cambió la URL
                        new_url = self.page.url
                        if new_url != current_url:
                            self.current_url = new_url
                            return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error navegando: {e}")
            return False