# -*- coding: utf-8 -*-
"""
Herramientas de extracción de productos para MercadoLibre México
"""

import re
from datetime import datetime
from dataclasses import asdict
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
from fastmcp import Context
from fastmcp.exceptions import ToolError

from browser.browser import MercadoLibreBrowser
from models.product import ProductData, PriceStatistics, ExtractionResult


class ProductTools:
    """Herramientas para extracción de datos de productos"""
    
    def __init__(self, browser: MercadoLibreBrowser):
        self.browser = browser
    
    async def extract_products(
        self,
        limit: int = 20,
        custom_selectors: Optional[Dict[str, str]] = None,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Extrae datos de productos de la página actual.
        
        Args:
            limit: Número máximo de productos a extraer
            custom_selectors: Selectores personalizados para elementos específicos
            ctx: Contexto de FastMCP
        
        Returns:
            Lista de productos extraídos con sus datos
        """
        if ctx:
            await ctx.info(f"Extrayendo hasta {limit} productos")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            # Usar selectores por defecto o personalizados
            selectors = self.browser.config.DEFAULT_SELECTORS.copy()
            if custom_selectors:
                selectors.update(custom_selectors)
            
            # Encontrar tarjetas de productos
            product_cards = await self.browser.page.query_selector_all(selectors['product_card'])
            
            if not product_cards:
                raise ToolError("No se encontraron productos en la página")
            
            products = []
            extraction_errors = []
            
            for i, card in enumerate(product_cards[:limit]):
                if ctx and i % 5 == 0:  # Reportar progreso cada 5 productos
                    await ctx.report_progress(progress=i, total=min(len(product_cards), limit))
                
                try:
                    product = await self._extract_single_product(card, selectors)
                    if product.title:  # Solo agregar si tiene título
                        products.append(asdict(product))
                    
                except Exception as e:
                    extraction_errors.append({
                        'product_index': i,
                        'error': str(e)
                    })
            
            # Estadísticas de precios
            price_stats = self._calculate_price_stats(products)
            
            result = {
                'extraction_info': {
                    'products_found': len(product_cards),
                    'products_extracted': len(products),
                    'extraction_errors': len(extraction_errors),
                    'selectors_used': selectors,
                    'page_url': self.browser.page.url,
                    'timestamp': datetime.now().isoformat()
                },
                'price_statistics': price_stats.__dict__ if price_stats else None,
                'products': products,
                'errors': extraction_errors if extraction_errors else None
            }
            
            if ctx:
                await ctx.info(f"Extracción completada: {len(products)} productos de {len(product_cards)}")
                await ctx.report_progress(progress=limit, total=limit)
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error extrayendo productos: {str(e)}")
            raise ToolError(f"Error extrayendo productos: {str(e)}")
    
    async def _extract_single_product(self, card, selectors: Dict[str, str]) -> ProductData:
        """Extrae datos de un solo producto"""
        
        async def safe_extract_text(parent, selector_key):
            """Extrae texto de manera segura"""
            if selector_key not in selectors:
                return None
            try:
                element = await parent.query_selector(selectors[selector_key])
                if element:
                    text = await element.inner_text()
                    return text.strip() if text else None
            except:
                pass
            return None
        
        async def safe_extract_attribute(parent, selector_key, attribute):
            """Extrae atributo de manera segura"""
            if selector_key not in selectors:
                return None
            try:
                element = await parent.query_selector(selectors[selector_key])
                if element:
                    return await element.get_attribute(attribute)
            except:
                pass
            return None
        
        # Extraer datos básicos
        title = await safe_extract_text(card, 'title')
        if not title:
            title = "Producto sin título"
        
        price = await safe_extract_text(card, 'price')
        if price and not price.startswith('$'):
            price = f"${price}"
        
        original_price = await safe_extract_text(card, 'original_price')
        
        # Calcular descuento
        discount = None
        if original_price and price:
            try:
                orig_num = float(re.sub(r'[^\d.]', '', original_price))
                curr_num = float(re.sub(r'[^\d.]', '', price))
                if orig_num > curr_num:
                    discount_pct = ((orig_num - curr_num) / orig_num) * 100
                    discount = f"{discount_pct:.0f}% OFF"
            except:
                pass
        
        # URL del producto
        product_url = await safe_extract_attribute(card, 'link', 'href')
        if product_url and product_url.startswith('/'):
            product_url = urljoin(self.browser.config.BASE_URL, product_url)
        
        # URL de imagen
        image_url = await safe_extract_attribute(card, 'image', 'src')
        
        # Otros datos
        shipping = await safe_extract_text(card, 'shipping')
        seller = await safe_extract_text(card, 'seller')
        
        return ProductData(
            title=title,
            price=price,
            original_price=original_price,
            discount=discount,
            url=product_url,
            image_url=image_url,
            shipping=shipping,
            seller=seller
        )
    
    def _calculate_price_stats(self, products: List[Dict]) -> Optional[PriceStatistics]:
        """Calcula estadísticas de precios"""
        prices = []
        for product in products:
            if product.get('price'):
                try:
                    price_num = float(re.sub(r'[^\d.]', '', product['price']))
                    prices.append(price_num)
                except:
                    continue
        
        if not prices:
            return None
        
        return PriceStatistics(
            total_products_with_price=len(prices),
            average_price_mxn=round(sum(prices) / len(prices), 2),
            min_price_mxn=min(prices),
            max_price_mxn=max(prices),
            products_with_discount=len([p for p in products if p.get('discount')])
        )