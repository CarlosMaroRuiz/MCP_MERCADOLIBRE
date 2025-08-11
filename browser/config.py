from typing import Dict, List


class BrowserConfig:
    """Configuración del navegador Playwright con anti-detección mejorada"""
    
    # Configuración del navegador
    HEADLESS = True  # Cambiar a False para debugging
    TIMEOUT = 60000  # Aumentado a 60 segundos
    
    # Argumentos del navegador mejorados para evadir detección
    BROWSER_ARGS = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--disable-features=VizDisplayCompositor',
        '--disable-background-networking',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--disable-blink-features=AutomationControlled',
        '--disable-ipc-flooding-protection',
        '--disable-web-security',
        '--disable-features=TranslateUI',
        '--disable-default-apps',
        '--no-default-browser-check',
        '--window-size=1366,768',
        '--start-maximized',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-images',  # Cargar más rápido
        '--disable-javascript',  # Comentar si necesitas JS
    ]
    
    # Configuración del viewport
    VIEWPORT = {
        'width': 1366,
        'height': 768
    }
    
    # User Agents múltiples para rotación
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    
    # User Agent por defecto
    USER_AGENT = USER_AGENTS[0]
    
    # Headers adicionales para parecer más humano
    EXTRA_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    # Configuración de localización
    LOCALE = 'es-MX'
    TIMEZONE = 'America/Mexico_City'
    
    # URLs con fallback
    BASE_URLS = [
        "https://www.mercadolibre.com.mx",
        "https://mercadolibre.com.mx",
        "https://listado.mercadolibre.com.mx"  # URL alternativa
    ]
    BASE_URL = BASE_URLS[0]
    
    VALID_DOMAINS = [
        'www.mercadolibre.com.mx', 
        'mercadolibre.com.mx',
        'listado.mercadolibre.com.mx',
        'articulo.mercadolibre.com.mx'
    ]
    
    # Configuración de retry
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # segundos entre reintentos
    
    # Configuración de delays para parecer humano
    HUMAN_DELAYS = {
        'page_load': (2, 4),  # segundos de espera después de cargar página
        'between_actions': (0.5, 1.5),  # entre acciones
        'typing': (0.1, 0.3),  # entre caracteres al escribir
    }
    
    # Selectores por defecto para extracción (actualizados)
    DEFAULT_SELECTORS = {
        'product_card': '.ui-search-result, .ui-search-result__wrapper',
        'title': '.ui-search-item__title, .ui-search-item__title-label',
        'price': '.andes-money-amount__fraction, .price-tag-fraction',
        'original_price': '.andes-money-amount--previous, .price-tag-original',
        'link': 'h2.ui-search-item__title a, .ui-search-item__title-label a, .ui-search-link',
        'image': '.ui-search-result-image__element, .ui-search-result__image img',
        'shipping': '.ui-search-item__shipping, .ui-search-shipping',
        'seller': '.ui-search-official-store-label, .ui-search-item__seller'
    }
    
    # Selectores de búsqueda con fallbacks
    SEARCH_SELECTORS = [
        'input[placeholder*="Buscar productos"]',
        'input.nav-search-input',
        'input[data-testid="cb1-edit"]',
        '#cb1-edit',
        'input[name="as_word"]',
        '.nav-search-input',
        'input[type="text"][placeholder*="buscar" i]'
    ]
    
    # Selectores de paginación
    PAGINATION_SELECTORS = {
        'next': [
            'a.andes-pagination__button--next:not(.andes-pagination__button--disabled)',
            'a[title="Siguiente"]:not(.disabled)',
            '.andes-pagination__button[aria-label*="Siguiente"]:not(.disabled)',
            'a[href*="Desde_"]:contains("Siguiente")'
        ],
        'previous': [
            'a.andes-pagination__button--previous:not(.andes-pagination__button--disabled)',
            'a[title="Anterior"]:not(.disabled)',
            '.andes-pagination__button[aria-label*="Anterior"]:not(.disabled)'
        ]
    }
    
    # Configuración de proxy (opcional)
    PROXY_CONFIG = {
        'enabled': False,
        'server': None,  # 'http://proxy-server:port'
        'username': None,
        'password': None
    }
    
    # Selectores por tipo de elemento
    SELECTOR_PATTERNS = {
        'products': [
            '.ui-search-result',
            '.ui-search-result__wrapper',
            '[data-testid="result-item"]',
            '.shops__item-container',
            '.item__info-container',
            '.ui-search-item'
        ],
        'prices': [
            '.andes-money-amount__fraction',
            '.price-tag-fraction',
            '.ui-search-price__part',
            '.andes-money-amount__digits',
            '.price-tag-symbol + .price-tag-fraction'
        ],
        'titles': [
            '.ui-search-item__title',
            '.ui-search-item__title-label',
            'h2.ui-search-item__title',
            '.ui-search-item__title a',
            '.ui-search-link'
        ],
        'navigation': [
            '.andes-pagination__button',
            '.andes-pagination__button--next',
            '.andes-pagination__button--previous',
            'a[title="Siguiente"]',
            'a[title="Anterior"]'
        ],
        'search': [
            'input[placeholder*="Buscar productos"]',
            'input.nav-search-input',
            '#cb1-edit',
            '.nav-search-button',
            'button[aria-label="Buscar"]'
        ]
    }