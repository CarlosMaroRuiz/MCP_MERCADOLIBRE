#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada principal para el servidor MCP de MercadoLibre México
"""

import sys
import logging
from pathlib import Path

# Agregar el directorio del proyecto al path para importaciones
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Ahora podemos importar el servidor
from server import create_server


def main():
    """Función principal"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Iniciando servidor MCP de MercadoLibre México")
    
    try:
        # Crear y ejecutar servidor
        server = create_server()
        
        # Ejecutar con transporte stdio por defecto
        server.run(transport="streamable-http")
        #server.run()
        
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
    except Exception as e:
        logger.error(f"Error ejecutando servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()