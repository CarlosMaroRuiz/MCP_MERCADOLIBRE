"""
Herramientas de descubrimiento y prueba de selectores CSS
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from fastmcp import Context
from fastmcp.exceptions import ToolError

from browser.browser import MercadoLibreBrowser
from models.selectors import DiscoveredSelector, SelectorAnalysis, SelectorTestResult


class SelectorTools:
    """Herramientas para descubrimiento y prueba de selectores"""
    
    def __init__(self, browser: MercadoLibreBrowser):
        self.browser = browser
    
    async def discover_selectors(
        self,
        element_type: str = "products",
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Descubre selectores CSS útiles en la página actual.
        
        Args:
            element_type: Tipo de elementos a buscar (products, navigation, search, prices, titles)
            ctx: Contexto de FastMCP
        
        Returns:
            Lista de selectores descubiertos con información de utilidad
        """
        if ctx:
            await ctx.info(f"Descubriendo selectores para: {element_type}")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            # JavaScript para descubrir selectores específicos
            js_discovery = self._get_discovery_javascript()
            discovered_selectors_raw = await self.browser.page.evaluate(js_discovery, element_type)
            
            # Convertir a objetos tipados
            discovered_selectors = [
                DiscoveredSelector(
                    selector=s['selector'],
                    confidence=s['confidence'],
                    description=s['description'],
                    element_count=s['element_count']
                ) for s in discovered_selectors_raw
            ]
            
            page_info = await self.browser.get_page_info()
            
            result = {
                'element_type': element_type,
                'page_info': page_info.__dict__,
                'selectors_found': len(discovered_selectors),
                'selectors': [s.__dict__ for s in discovered_selectors],
                'timestamp': datetime.now().isoformat(),
                'recommendations': self._generate_recommendations(discovered_selectors, element_type)
            }
            
            if ctx:
                await ctx.info(f"Descubiertos {len(discovered_selectors)} selectores para {element_type}")
            
            return result
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error descubriendo selectores: {str(e)}")
            raise ToolError(f"Error descubriendo selectores: {str(e)}")
    
    async def test_selector(
        self,
        selector: str,
        extract_text: bool = True,
        check_visibility: bool = True,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Prueba un selector CSS específico para evaluar su utilidad.
        
        Args:
            selector: Selector CSS a probar
            extract_text: Si extraer texto de muestra de los elementos encontrados
            check_visibility: Si verificar la visibilidad de los elementos
            ctx: Contexto de FastMCP
        
        Returns:
            Resultado detallado de la prueba del selector
        """
        if ctx:
            await ctx.info(f"Probando selector: {selector}")
        
        try:
            if not self.browser.page:
                raise ToolError("No hay ninguna página cargada")
            
            # Encontrar elementos
            elements = await self.browser.page.query_selector_all(selector)
            element_count = len(elements)
            
            if element_count == 0:
                return SelectorTestResult(
                    selector=selector,
                    success=False,
                    element_count=0,
                    message='No se encontraron elementos',
                    timestamp=datetime.now().isoformat()
                ).__dict__
            
            # Analizar elementos encontrados
            analysis = await self._analyze_elements(
                elements[:10],  # Analizar primeros 10
                extract_text,
                check_visibility
            )
            
            # Calcular puntuación de utilidad
            utility_score, recommendations = self._calculate_utility_score(
                element_count, analysis, selector
            )
            
            result = SelectorTestResult(
                selector=selector,
                success=True,
                element_count=element_count,
                analysis=analysis,
                utility_score=min(utility_score, 1.0),
                recommendations=recommendations,
                is_useful=utility_score > 0.6,
                timestamp=datetime.now().isoformat()
            )
            
            if ctx:
                await ctx.info(f"Selector probado: {element_count} elementos, utilidad: {utility_score:.2f}")
            
            return result.__dict__
            
        except Exception as e:
            if ctx:
                await ctx.error(f"Error probando selector: {str(e)}")
            raise ToolError(f"Error probando selector {selector}: {str(e)}")
    
    async def _analyze_elements(
        self, 
        elements: List, 
        extract_text: bool, 
        check_visibility: bool
    ) -> SelectorAnalysis:
        """Analiza una lista de elementos"""
        analysis = SelectorAnalysis(
            element_count=len(elements),
            visible_elements=0,
            sample_texts=[],
            element_types=[],
            has_useful_content=False
        )
        
        for i, element in enumerate(elements):
            try:
                # Tipo de elemento
                tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                analysis.element_types.append(tag_name)
                
                # Visibilidad
                if check_visibility:
                    is_visible = await element.is_visible()
                    if is_visible:
                        analysis.visible_elements += 1
                
                # Texto de muestra
                if extract_text:
                    text = await element.inner_text()
                    if text and text.strip():
                        text_sample = text.strip()[:100]
                        analysis.sample_texts.append({
                            'index': i,
                            'text': text_sample,
                            'length': len(text.strip())
                        })
                        
                        # Verificar si tiene contenido útil
                        if len(text.strip()) > 10:
                            analysis.has_useful_content = True
                
            except Exception as e:
                analysis.sample_texts.append({
                    'index': i,
                    'error': str(e)
                })
        
        return analysis
    
    def _calculate_utility_score(
        self, 
        element_count: int, 
        analysis: SelectorAnalysis, 
        selector: str
    ) -> tuple[float, List[str]]:
        """Calcula puntuación de utilidad y recomendaciones"""
        utility_score = 0.0
        recommendations = []
        
        if element_count > 0:
            utility_score += 0.3
        
        if analysis.visible_elements > 0:
            visibility_ratio = analysis.visible_elements / min(element_count, 10)
            utility_score += visibility_ratio * 0.3
            
            if visibility_ratio < 0.5:
                recommendations.append("Muchos elementos no son visibles")
        
        if analysis.has_useful_content:
            utility_score += 0.4
        
        # Recomendaciones específicas
        if element_count > 100:
            recommendations.append("Demasiados elementos - considere un selector más específico")
        elif element_count < 3 and 'product' in selector.lower():
            recommendations.append("Pocos productos encontrados - verifique que esté en página de resultados")
        
        # Tipos de elementos únicos
        unique_types = list(set(analysis.element_types))
        if len(unique_types) > 1:
            recommendations.append(f"Selector encuentra múltiples tipos: {', '.join(unique_types)}")
        
        return utility_score, recommendations
    
    def _generate_recommendations(
        self, 
        selectors: List[DiscoveredSelector], 
        element_type: str
    ) -> List[str]:
        """Genera recomendaciones basadas en selectores descubiertos"""
        recommendations = []
        
        if selectors:
            best_selector = selectors[0]
            recommendations.append(
                f"Mejor selector: {best_selector.selector} (confianza: {best_selector.confidence:.1f})"
            )
            
            high_confidence = [s for s in selectors if s.confidence >= 0.8]
            if len(high_confidence) > 1:
                recommendations.append(f"{len(high_confidence)} selectores de alta confianza disponibles")
        else:
            recommendations.append(f"No se encontraron selectores para {element_type}")
        
        return recommendations
    
    def _get_discovery_javascript(self) -> str:
        """Retorna el código JavaScript para descubrir selectores"""
        return """
        (elementType) => {
            const discovered = [];
            
            function addSelector(selector, confidence, description, elementCount) {
                if (elementCount > 0) {
                    discovered.push({
                        selector: selector,
                        confidence: confidence,
                        description: description,
                        element_count: elementCount
                    });
                }
            }
            
            if (elementType === 'products') {
                const productSelectors = [
                    '.ui-search-result',
                    '.ui-search-result__wrapper',
                    '[data-testid="result-item"]',
                    '.shops__item-container',
                    '.item__info-container'
                ];
                
                productSelectors.forEach(sel => {
                    const elements = document.querySelectorAll(sel);
                    if (elements.length > 0) {
                        addSelector(sel, 0.9, 'Tarjeta de producto', elements.length);
                    }
                });
            }
            
            else if (elementType === 'prices') {
                const priceSelectors = [
                    '.andes-money-amount__fraction',
                    '.price-tag-fraction',
                    '.ui-search-price__part',
                    '.andes-money-amount__digits'
                ];
                
                priceSelectors.forEach(sel => {
                    const elements = document.querySelectorAll(sel);
                    addSelector(sel, 0.9, 'Precio de producto', elements.length);
                });
            }
            
            else if (elementType === 'titles') {
                const titleSelectors = [
                    '.ui-search-item__title',
                    '.ui-search-item__title-label',
                    'h2.ui-search-item__title',
                    '.ui-search-item__title a'
                ];
                
                titleSelectors.forEach(sel => {
                    const elements = document.querySelectorAll(sel);
                    addSelector(sel, 0.9, 'Título de producto', elements.length);
                });
            }
            
            else if (elementType === 'navigation') {
                const navSelectors = [
                    '.andes-pagination__button',
                    '.andes-pagination__button--next',
                    '.andes-pagination__button--previous',
                    'a[title="Siguiente"]',
                    'a[title="Anterior"]'
                ];
                
                navSelectors.forEach(sel => {
                    const elements = document.querySelectorAll(sel);
                    addSelector(sel, 0.8, 'Navegación/Paginación', elements.length);
                });
            }
            
            return discovered.sort((a, b) => {
                if (a.confidence !== b.confidence) {
                    return b.confidence - a.confidence;
                }
                return b.element_count - a.element_count;
            });
        }
        """