from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import logging
import validators
import topics

class Bot:

    YOUTUBE_DOWNLOAD = 0


    def __init__(self, token: str, chat_id: int) -> None:
        self.__token = token
        self.__chat_id = chat_id

    async def __video_download_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.info("got YouTube download request")
        await update.message.reply_text("Enter a video url")
        
        return self.YOUTUBE_DOWNLOAD
    
    async def __video_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        url = update.message.text
        if not validators.url(url):
            await update.message.reply_text("Invalid url, try again")
            return self.YOUTUBE_DOWNLOAD
        
        self.__publish_callback(topics.VIDEO_DOWNLOAD, url)
        await update.message.reply_text("Video download queued")
        return ConversationHandler.END

    async def __get_ip_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__publish_callback(topics.GET_IP_ADDRESS, None)
        await update.message.reply_text("Getting IP address...")
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
                CommandHandler("ytdownload", self.__video_download_start, filters=filters.Chat(self.__chat_id)),
                CommandHandler("ipaddress", self.__get_ip_address, filters=filters.Chat(self.__chat_id))
            ],
            states={
                self.YOUTUBE_DOWNLOAD: [MessageHandler(filters=filters.TEXT, callback=self.__video_download)]
            },
            fallbacks=[CommandHandler("cancel", self.__cancel)]
        )

        self.__app.add_handler(conversation_handler)
        self.__app.run_polling()