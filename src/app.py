import chainlit as cl

# Esta función se ejecuta cuando empieza un chat nuevo
@cl.on_chat_start
async def start():
    await cl.Message(
        content="¡Bienvenido al Chat Multi-Modelo! \nSistema inicializado correctamente."
    ).send()


# Esta función se ejecuta cada vez que el usuario envía un mensaje
@cl.on_message
async def main(message: cl.Message):
    # AQUÍ es donde luego conectaremos a Ollama/OpenAI
    # Por ahora, simulamos una respuesta.
    user_input = message.content

    response = f"Recibí tu mensaje: '{user_input}'. \n(En la Fase 2 conectaremos los LLMs aquí)."

    await cl.Message(content=response).send()
