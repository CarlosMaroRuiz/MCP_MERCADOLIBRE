import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configurar el servidor MCP
server = MCPServerStreamableHTTP('http://localhost:8000/mcp')

# Crear agente con configuración optimizada
agent = Agent(
    "google-gla:gemini-2.5-pro", 
    toolsets=[server],
    model_settings={
        'max_retries': 2,
        'timeout': 30,
    }
)

class SearchResult(BaseModel):
    """Resultado estructurado de la búsqueda inteligente"""
    status: str = Field(description="Estado de la búsqueda: success, error, retry")
    search_query: str = Field(description="Query original de búsqueda")
    products_found: List[dict] = Field(default=[], description="Lista de productos encontrados")
    total_products: int = Field(default=0, description="Número total de productos")
    error_message: Optional[str] = Field(default=None, description="Mensaje de error si aplica")
    prevention_applied: bool = Field(default=False, description="Si se aplicaron consejos de prevención")
    execution_steps: List[str] = Field(default=[], description="Pasos ejecutados durante la búsqueda")
    usage_stats: Optional[dict] = Field(default=None, description="Estadísticas de uso del modelo")

async def intelligent_search(query: str) -> SearchResult:
    """
    Búsqueda inteligente con manejo de errores y aprendizaje automático
    """
    execution_steps = []
    
    try:
        logger.info(f"🚀 Iniciando búsqueda inteligente: {query}")
        
        async with agent:
            # PASO 1: Obtener consejos de prevención
            execution_steps.append("Obteniendo consejos de prevención")
            prevention_result = await agent.run(
                f"""
                Antes de buscar '{query}', usa get_prevention_advice para obtener consejos sobre:
                1. Herramienta: extract_products
                2. Herramienta: search_products
                
                Aplica cualquier consejo que encuentres para evitar errores conocidos.
                """,
                output_type=str
            )
            
            logger.info(f"🛡️ Consejos de prevención: {prevention_result.output}")
            execution_steps.append(f"Consejos aplicados: {prevention_result.output}")
            
            # PASO 2: Ejecutar búsqueda inteligente con manejo automático de errores
            execution_steps.append("Ejecutando búsqueda con smart_search_and_extract")
            search_result = await agent.run(
                f"""
                Usa smart_search_and_extract para buscar '{query}' con estas configuraciones:
                - search_query: {query}
                - max_products: 10
                - auto_prevent_errors: true
                
                Si encuentras errores:
                1. Usa discover_selectors para encontrar selectores correctos
                2. Actualiza los selectores y reintenta con extract_products
                3. Si continúan los errores, usa get_error_statistics para diagnosticar
                
                Devuelve un reporte detallado de los productos encontrados.
                """,
                output_type=str
            )
            
            logger.info(f"✅ Búsqueda completada")
            execution_steps.append("Búsqueda completada exitosamente")
            
            # Extraer estadísticas de uso
            usage_stats = {
                "requests": search_result.usage().requests if hasattr(search_result.usage(), 'requests') else 0,
                "total_tokens": search_result.usage().total_tokens if hasattr(search_result.usage(), 'total_tokens') else 0,
                "timestamp": search_result.timestamp().isoformat()
            }
            
            return SearchResult(
                status="success",
                search_query=query,
                products_found=[],  # Se poblará con el parsing del resultado
                total_products=0,   # Se calculará después
                prevention_applied=True,
                execution_steps=execution_steps,
                usage_stats=usage_stats
            )
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error en búsqueda: {error_msg}")
        execution_steps.append(f"Error encontrado: {error_msg}")
        
        # Manejo inteligente de errores específicos
        if "exceeded max retries" in error_msg.lower():
            return await handle_max_retries_error(query, execution_steps)
        elif "timeout" in error_msg.lower():
            return await handle_timeout_error(query, execution_steps)
        else:
            return SearchResult(
                status="error",
                search_query=query,
                error_message=error_msg,
                execution_steps=execution_steps
            )

async def handle_max_retries_error(query: str, execution_steps: List[str]) -> SearchResult:
    """Manejo específico para errores de máximo de reintentos"""
    try:
        execution_steps.append("Intentando diagnóstico de reintentos excedidos")
        
        async with agent:
            diagnostic = await agent.run(
                """
                El sistema excedió el máximo de reintentos. Realiza un diagnóstico:
                1. Usa get_current_page_info para verificar el estado actual
                2. Usa discover_selectors para encontrar selectores válidos
                3. Usa get_error_statistics para revisar errores recientes
                4. Proporciona un resumen del estado del sistema
                """,
                output_type=str
            )
            
            execution_steps.append(f"Diagnóstico completado: {diagnostic.output}")
            
            return SearchResult(
                status="error",
                search_query=query,
                error_message="Máximo de reintentos excedido",
                execution_steps=execution_steps
            )
    except:
        execution_steps.append("Diagnóstico falló - error crítico")
        return SearchResult(
            status="error",
            search_query=query,
            error_message="Error crítico: diagnóstico falló",
            execution_steps=execution_steps
        )

async def handle_timeout_error(query: str, execution_steps: List[str]) -> SearchResult:
    """Manejo específico para errores de timeout"""
    execution_steps.append("Manejando error de timeout")
    
    try:
        # Intentar una búsqueda más simple
        async with agent:
            simple_result = await agent.run(
                f"""
                Timeout detectado. Intenta una búsqueda SIMPLE:
                1. go_to_home
                2. search_products con query: {query} (solo búsqueda básica)
                3. NO extraer productos, solo confirmar que la búsqueda funciona
                """,
                output_type=str
            )
            
            execution_steps.append("Búsqueda simple completada tras timeout")
            
            return SearchResult(
                status="success",
                search_query=query,
                error_message="Búsqueda completada con timeout (versión simplificada)",
                execution_steps=execution_steps
            )
    except:
        return SearchResult(
            status="error",
            search_query=query,
            error_message="Timeout - imposible conectar",
            execution_steps=execution_steps
        )

async def get_system_insights() -> dict:
    """Obtiene insights del sistema de aprendizaje"""
    try:
        async with agent:
            insights_result = await agent.run(
                """
                Usa get_learning_insights para obtener información sobre:
                1. Errores más comunes
                2. Patrones de fallos
                3. Recomendaciones de mejora
                """,
                output_type=str
            )
            
            return {
                "insights": insights_result.output,
                "timestamp": insights_result.timestamp().isoformat(),
                "usage": {
                    "requests": insights_result.usage().requests,
                    "tokens": insights_result.usage().total_tokens
                }
            }
    except Exception as e:
        return {"error": str(e)}

async def main():
    """Función principal del agente inteligente"""
    query = 'buscame una laptop gamer barata'
    
    print(f"🤖 BuildAgente - Búsqueda Inteligente")
    print(f"📝 Query: {query}")
    print("=" * 50)
    
    # Ejecutar búsqueda inteligente
    result = await intelligent_search(query)
    
    # Mostrar resultados
    print(f"\n📊 RESULTADO:")
    print(f"Estado: {result.status}")
    print(f"Query: {result.search_query}")
    
    if result.status == "success":
        print(f"✅ Búsqueda exitosa")
        if result.usage_stats:
            print(f"📈 Uso: {result.usage_stats['total_tokens']} tokens, {result.usage_stats['requests']} requests")
    else:
        print(f"❌ Error: {result.error_message}")
    
    print(f"\n🔄 Pasos ejecutados:")
    for i, step in enumerate(result.execution_steps, 1):
        print(f"  {i}. {step}")
    
    # Obtener insights del sistema si hay errores
    if result.status == "error":
        print(f"\n🧠 Obteniendo insights del sistema...")
        insights = await get_system_insights()
        if "error" not in insights:
            print(f"💡 Insights: {insights['insights']}")
        else:
            print(f"⚠️ No se pudieron obtener insights: {insights['error']}")

# Función de testing rápido
async def quick_test():
    """Test rápido del agente"""
    try:
        async with agent:
            test_result = await agent.run(
                """
                Realiza un test rápido del sistema:
                1. go_to_home
                2. get_current_page_info
                3. Reporta si el sistema está funcionando
                """,
                output_type=str
            )
            
            print(f"🧪 Test resultado: {test_result.output}")
            return True
    except Exception as e:
        print(f"🚨 Test falló: {e}")
        return False

if __name__ == "__main__":
    print("🔧 BuildAgente - Agente Inteligente v2.0")
    print("Opciones:")
    print("1. Búsqueda inteligente completa")
    print("2. Test rápido del sistema")
    
    choice = input("Elige (1 o 2): ").strip()
    
    if choice == "2":
        result = asyncio.run(quick_test())
        print(f"Test {'exitoso' if result else 'falló'}")
    else:
        asyncio.run(main())