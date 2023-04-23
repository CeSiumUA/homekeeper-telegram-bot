from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import logging
import validators
import topics

class Bot:
    def __init__(self) -> None:
        pass

    async def __video_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        url = update.message.text
        logging.info(f"got YouTube download request, url: {url}")
        if not validators.url(url):
            await update.message.reply_text("Invalid url")
        else:
            self.__publish_callback(topics.VIDEO_DOWNLOAD, url)
            await update.message.reply_text("Video download queued")
        return ConversationHandler.END

    def start_bot(self, token: str, publish_callback):
        app = Application.builder().token(token=token).build()

        self.__publish_callback = publish_callback

        conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler("video-download", self.__video_download)
            ]
        )

        app.add_handler(conversation_handler)

        app.run_polling()