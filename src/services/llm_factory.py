"""Gestor de modelos LLM (placeholder).

Aquí se centralizará la creación/configuración de los modelos LLM.
"""

from typing import Any


def get_llm(name: str, **kwargs) -> Any:
    """Devuelve una instancia del LLM solicitado (placeholder).

    Reemplazar por creación real de clientes (OpenAI, llama, etc.).
    """
    # Placeholder: devolver un dict que represente la configuración
    return {"model": name, "config": kwargs}
