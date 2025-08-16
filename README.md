## Aprendizaje en la integración MCP con Deepseek y Claude

* Claude ha podido usar MCP correctamente sin inconvenientes.
* Deepseek presentó un problema interno relacionado con tipos de datos.
  Este problema está asociado con la librería `pydanticAi`, que utiliza internamente `Union` para parsear y estructurar los datos.
  Sin embargo, con Deepseek esto provoca fallos que no ocurren con Claude.
* Para solucionar este inconveniente, creé un *wrapper* que facilita una posible futura implementación de Deepseek como agente capaz de conectarse a servidores MCP.

---

Repositorio:
[https://github.com/CarlosMaroRuiz/deepseek-mcp-client](https://github.com/CarlosMaroRuiz/deepseek-mcp-client)

---

