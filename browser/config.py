from typing import Dict, List


class BrowserConfig:
    """Configuración del navegador Playwright"""
    
    # Configuración del navegador
    HEADLESS = True
    TIMEOUT = 30000
    
    # Argumentos del navegador
    BROWSER_ARGS = [
        '--no-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-web-security',
        '--window-size=1366,768'
    ]
    
    # Configuración del viewport
    VIEWPORT = {
        'width': 1366,
        'height': 768
    }
    
    # User Agent
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # Configuración de localización
    LOCALE = 'es-MX'
    TIMEZONE = 'America/Mexico_City'
    
    # URLs base
    BASE_URL = "https://www.mercadolibre.com.mx"
    VALID_DOMAINS = ['www.mercadolibre.com.mx', 'mercadolibre.com.mx']
    
    # Selectores por defecto para extracción
    DEFAULT_SELECTORS = {
        'product_card': '.ui-search-result',
        'title': '.ui-search-item__title',
        'price': '.andes-money-amount__fraction',
        'original_price': '.andes-money-amount--previous',
        'link': 'h2.ui-search-item__title a, .ui-search-item__title-label a',
        'image': '.ui-search-result-image__element',
        'shipping': '.ui-search-item__shipping',
        'seller': '.ui-search-official-store-label'
    }
    
    # Selectores de búsqueda
    SEARCH_SELECTORS = [
        'input.nav-search-input',
        'input[placeholder*="Buscar"]',
        'input[data-testid="cb1-edit"]',
        '#cb1-edit',
        'input[name="as_word"]'
    ]
    
    # Selectores de paginación
    PAGINATION_SELECTORS = {
        'next': [
            'a.andes-pagination__button--next',
            'a[title="Siguiente"]',
            '.andes-pagination__button[aria-label*="Siguiente"]'
        ],
        'previous': [
            'a.andes-pagination__button--previous',
            'a[title="Anterior"]',
            '.andes-pagination__button[aria-label*="Anterior"]'
        ]
    }
    
    # Selectores por tipo de elemento
    SELECTOR_PATTERNS = {
        'products': [
            '.ui-search-result',
            '.ui-search-result__wrapper',
            '[data-testid="result-item"]',
            '.shops__item-container',
            '.item__info-container'
        ],
        'prices': [
            '.andes-money-amount__fraction',
            '.price-tag-fraction',
            '.ui-search-price__part',
            '.andes-money-amount__digits'
        ],
        'titles': [
            '.ui-search-item__title',
            '.ui-search-item__title-label',
            'h2.ui-search-item__title',
            '.ui-search-item__title a'
        ],
        'navigation': [
            '.andes-pagination__button',
            '.andes-pagination__button--next',
            '.andes-pagination__button--previous',
            'a[title="Siguiente"]',
            'a[title="Anterior"]'
        ],
        'search': [
            'input.nav-search-input',
            'input[placeholder*="Buscar"]',
            '#cb1-edit',
            '.nav-search-button',
            'button[aria-label="Buscar"]'
        ]
    }