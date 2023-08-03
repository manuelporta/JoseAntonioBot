import os
import telegram
from telegram import Update
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
)

import comandos


if __name__ == "__main__":
    print("Primero que nada: Cómo están los máquinas?")

    app = Application.builder().token(os.environ.get("TG_BOT")).build()
    # app = Application.builder().token(os.environ.get("TG_BOT_TEST")).build()

    app.add_handler(CommandHandler("hola", comandos.comando_hola))
    app.add_handler(CommandHandler("mimimi", comandos.comando_mimimi))
    app.add_handler(CommandHandler("pistas", comandos.comando_pistas))
    app.add_handler(CommandHandler("kdise", comandos.comando_audio))

    app.add_handler(MessageHandler(filters.TEXT, comandos.respuesta_rima))

    app.add_error_handler(comandos.error)

    print("Polling...")
    app.run_polling(poll_interval=5)

