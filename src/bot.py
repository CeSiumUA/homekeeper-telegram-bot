from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import logging
import validators
import topics

class Bot:
    def __init__(self, token: str, chat_id: int) -> None:
        self.__token = token
        self.__chat_id = chat_id

    async def __video_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        url = update.message.text
        logging.info(f"got YouTube download request, url: {url}")
        if not validators.url(url):
            await update.message.reply_text("Invalid url")
        else:
            self.__publish_callback(topics.VIDEO_DOWNLOAD, url)
            await update.message.reply_text("Video download queued")
        return ConversationHandler.END
    
    async def __cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END

    def send_message(self, message):
        self.__app.bot.send_message(self.__chat_id, text=message)

    def start_bot(self, publish_callback):
        self.__app = Application.builder().token(token=self.__token).build()

        self.__publish_callback = publish_callback

        conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler("download", self.__video_download, filters=filters.Chat(self.__chat_id))
            ],
            states={},
            fallbacks=[CommandHandler("cancel", self.__cancel)]
        )

        self.__app.add_handler(conversation_handler)
        self.__app.run_polling()