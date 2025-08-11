# -*- coding: utf-8 -*-
"""
Navegador mejorado para MercadoLibre México con manejo robusto de errores
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

from models.product import PageInfo
from .config import BrowserConfig


logger = logging.getLogger(__name__)


class MercadoLibreBrowser:
    """Navegador mejorado para MercadoLibre México con anti-detección"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_url = ""
        self.playwright = None
        self.retry_count = 0
        
    async def initialize(self, retry: bool = True):
        """Inicializar navegador con configuración mejorada"""
        if self.browser:
            return True
            
        try:
            self.playwright = await async_playwright().__aenter__()
            
            # Lanzar navegador con configuración anti-detección
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.HEADLESS,
                args=self.config.BROWSER_ARGS,
                slow_mo=50  # Simular comportamiento humano
            )
            
            # Crear contexto con configuración completa
            context_options = {
                'viewport': self.config.VIEWPORT,
                'user_agent': random.choice(self.config.USER_AGENTS),
                'locale': self.config.LOCALE,
                'timezone_id': self.config.TIMEZONE,
                'extra_http_headers': self.config.EXTRA_HEADERS,
                'java_script_enabled': True,
                'accept_downloads': False,
                'ignore_https_errors': True,
            }
            
            # Agregar proxy si está configurado
            if self.config.PROXY_CONFIG['enabled'] and self.config.PROXY_CONFIG['server']:
                context_options['proxy'] = {
                    'server': self.config.PROXY_CONFIG['server'],
                    'username': self.config.PROXY_CONFIG.get('username'),
                    'password': self.config.PROXY_CONFIG.get('password'),
                }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Configurar página con scripts anti-detección
            self.page = await self.context.new_page()
            
            # Eliminar propiedades de automatización
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                delete navigator.__proto__.webdriver;
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['es-MX', 'es', 'en-US', 'en'],
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });
                
                window.chrome = {
                    runtime: {},
                    // etc.
                };
                
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: async () => ({ state: 'granted' }),
                    }),
                });
            """)
            
            # Configurar timeouts
            self.page.set_default_timeout(self.config.TIMEOUT)
            self.page.set_default_navigation_timeout(self.config.TIMEOUT)
            
            logger.info("✅ Navegador inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando navegador: {e}")
            if retry and self.retry_count < self.config.MAX_RETRIES:
                self.retry_count += 1
                logger.info(f"🔄 Reintentando inicialización ({self.retry_count}/{self.config.MAX_RETRIES})")
                await asyncio.sleep(self.config.RETRY_DELAY)
                return await self.initialize(retry=False)
            return False
    
    async def close(self):
        """Cerrar navegador limpiamente"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.__aexit__(None, None, None)
                
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
            
            logger.info("✅ Navegador cerrado correctamente")
        except Exception as e:
            logger.error(f"⚠️ Error cerrando navegador: {e}")
    
    async def navigate(self, url: str, retry: bool = True) -> bool:
        """Navegar a URL específica con retry logic mejorado"""
        try:
            # Inicializar si es necesario
            if not await self.initialize():
                return False
            
            # Validar URL
            if not self.is_valid_ml_url(url):
                raise ValueError(f"URL no es de MercadoLibre México: {url}")
            
            logger.info(f"🌐 Navegando a: {url}")
            
            # Intentar navegación con diferentes estrategias
            success = await self._attempt_navigation(url)
            
            if success:
                # Esperar carga completa
                await self._wait_for_stable_load()
                self.current_url = self.page.url
                self.retry_count = 0  # Reset retry count on success
                logger.info(f"✅ Navegación exitosa: {self.current_url}")
                return True
            else:
                raise Exception("No se pudo completar la navegación")
                
        except Exception as e:
            logger.error(f"❌ Error navegando a {url}: {e}")
            
            if retry and self.retry_count < self.config.MAX_RETRIES:
                self.retry_count += 1
                logger.info(f"🔄 Reintentando navegación ({self.retry_count}/{self.config.MAX_RETRIES})")
                
                # Estrategias de recuperación
                await self._recovery_strategy()
                await asyncio.sleep(self.config.RETRY_DELAY * self.retry_count)
                
                return await self.navigate(url, retry=True)
            
            return False
    
    async def _attempt_navigation(self, url: str) -> bool:
        """Intenta navegar con diferentes estrategias"""
        strategies = [
            ('networkidle', self.config.TIMEOUT),
            ('domcontentloaded', self.config.TIMEOUT // 2),
            ('load', self.config.TIMEOUT // 3),
            (None, 15000)  # Sin wait_until, timeout corto
        ]
        
        for wait_until, timeout in strategies:
            try:
                logger.info(f"🔄 Intentando navegación con estrategia: {wait_until or 'none'}")
                
                if wait_until:
                    await self.page.goto(
                        url, 
                        wait_until=wait_until, 
                        timeout=timeout
                    )
                else:
                    await self.page.goto(url, timeout=timeout)
                
                # Verificar si la página se cargó
                if await self._is_page_loaded():
                    return True
                    
            except PlaywrightTimeoutError:
                logger.warning(f"⚠️ Timeout con estrategia {wait_until or 'none'}")
                continue
            except Exception as e:
                logger.warning(f"⚠️ Error con estrategia {wait_until or 'none'}: {e}")
                continue
        
        return False
    
    async def _is_page_loaded(self) -> bool:
        """Verifica si la página se cargó correctamente"""
        try:
            # Verificar que no estamos en página de error
            title = await self.page.title()
            url = self.page.url
            
            error_indicators = [
                'error', 'not found', '404', '503', '500',
                'blocked', 'denied', 'forbidden'
            ]
            
            if any(indicator in title.lower() for indicator in error_indicators):
                logger.warning(f"⚠️ Página de error detectada: {title}")
                return False
            
            if any(indicator in url.lower() for indicator in error_indicators):
                logger.warning(f"⚠️ URL de error detectada: {url}")
                return False
            
            # Verificar que hay contenido básico
            try:
                await self.page.wait_for_selector('body', timeout=5000)
                body_content = await self.page.evaluate('document.body.innerText.length')
                
                if body_content < 100:  # Muy poco contenido
                    logger.warning("⚠️ Página con muy poco contenido")
                    return False
                
                return True
                
            except:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verificando carga de página: {e}")
            return False
    
    async def _wait_for_stable_load(self):
        """Espera a que la página se estabilice"""
        try:
            # Esperar a que no haya requests pendientes
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Espera adicional para JavaScript
            await asyncio.sleep(random.uniform(*self.config.HUMAN_DELAYS['page_load']))
            
        except PlaywrightTimeoutError:
            # Si timeout, continuar anyway
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"⚠️ Error esperando estabilización: {e}")
    
    async def _recovery_strategy(self):
        """Estrategias de recuperación ante errores"""
        try:
            if self.page:
                # Intentar refrescar
                try:
                    await self.page.reload(timeout=10000)
                    await asyncio.sleep(2)
                except:
                    pass
                
                # Limpiar caché y cookies
                try:
                    await self.context.clear_cookies()
                    await self.context.clear_permissions()
                except:
                    pass
            
            # Si falló mucho, reinicializar completamente
            if self.retry_count >= 2:
                logger.info("🔄 Reinicializando navegador completamente")
                await self.close()
                await asyncio.sleep(3)
                
        except Exception as e:
            logger.warning(f"⚠️ Error en estrategia de recuperación: {e}")
    
    def is_valid_ml_url(self, url: str) -> bool:
        """Validar que la URL sea de MercadoLibre México"""
        try:
            parsed = urlparse(url)
            return parsed.netloc in self.config.VALID_DOMAINS
        except:
            return False
    
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
                    # Probar múltiples selectores
                    for selector in self.config.SELECTOR_PATTERNS['products']:
                        try:
                            product_cards = await self.page.query_selector_all(selector)
                            if product_cards:
                                product_cards_found = len(product_cards)
                                break
                        except:
                            continue
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
        if any(path in url for path in ['/search', 'listado.mercadolibre', 'q=']):
            return 'search_results'
        elif any(path in url for path in ['/p/', 'MLA', 'articulo.mercadolibre']):
            return 'product_detail'
        elif url in self.config.BASE_URLS or url.rstrip('/') in [u.rstrip('/') for u in self.config.BASE_URLS]:
            return 'homepage'
        else:
            return 'other'
    
    async def search(self, query: str) -> bool:
        """Realizar búsqueda en MercadoLibre con retry mejorado"""
        try:
            logger.info(f"🔍 Buscando: '{query}'")
            
            # Buscar caja de búsqueda con múltiples selectores
            search_box = None
            for selector in self.config.SEARCH_SELECTORS:
                try:
                    search_box = await self.page.query_selector(selector)
                    if search_box and await search_box.is_visible():
                        logger.info(f"✅ Caja de búsqueda encontrada: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                logger.error("❌ No se encontró caja de búsqueda")
                return False
            
            # Limpiar y escribir búsqueda
            await search_box.click()
            await asyncio.sleep(random.uniform(*self.config.HUMAN_DELAYS['between_actions']))
            
            # Limpiar campo
            await search_box.fill("")
            await asyncio.sleep(0.5)
            
            # Escribir con delay humano
            for char in query:
                await search_box.type(char)
                await asyncio.sleep(random.uniform(*self.config.HUMAN_DELAYS['typing']))
            
            await asyncio.sleep(random.uniform(*self.config.HUMAN_DELAYS['between_actions']))
            
            # Presionar Enter
            await search_box.press('Enter')
            
            # Esperar resultados
            await self._wait_for_stable_load()
            
            self.current_url = self.page.url
            
            # Verificar que llegamos a resultados
            if 'search' in self.current_url or 'listado' in self.current_url:
                logger.info(f"✅ Búsqueda exitosa: {self.current_url}")
                return True
            else:
                logger.warning(f"⚠️ URL inesperada después de búsqueda: {self.current_url}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {e}")
            return False
    
    async def navigate_pagination(self, direction: str = "next") -> bool:
        """Navegar páginas de resultados con manejo mejorado"""
        try:
            logger.info(f"📄 Navegando a página {direction}")
            
            current_url = self.page.url
            selectors = self.config.PAGINATION_SELECTORS.get(direction, [])
            
            for selector in selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible() and await element.is_enabled():
                        
                        # Scroll al elemento
                        await element.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        
                        # Click con delay humano
                        await element.click()
                        await self._wait_for_stable_load()
                        
                        # Verificar si cambió la URL
                        new_url = self.page.url
                        if new_url != current_url:
                            self.current_url = new_url
                            logger.info(f"✅ Navegación {direction} exitosa")
                            return True
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error con selector {selector}: {e}")
                    continue
            
            logger.warning(f"⚠️ No se pudo navegar {direction}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error navegando: {e}")
            return False