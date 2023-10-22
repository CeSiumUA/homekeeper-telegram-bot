from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import logging
import validators
import topics
import random
import asyncio

class TlBot:

    YOUTUBE_DOWNLOAD = 0


    def __init__(self, token: str, chat_id: int) -> None:
        self.__token = token
        self.__chat_id = chat_id
        self.__bot_context = None

    async def __video_download_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__bot_context = context
        logging.info("got YouTube download request")
        await update.message.reply_text("Enter a video url")
        return self.YOUTUBE_DOWNLOAD
    
    async def __video_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__bot_context = context
        url = update.message.text
        logging.info("got YouTube url %s\n", url)
        if not validators.url(url):
            logging.error("url %s is invalid\n", url)
            await update.message.reply_text("Invalid url, try again")
            return self.YOUTUBE_DOWNLOAD
        self.__publish_callback(topics.VIDEO_DOWNLOAD, url)
        await update.message.reply_text("Video download queued")
        return ConversationHandler.END

    async def __get_ip_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__bot_context = context
        logging.info("got ip address determination request")
        self.__publish_callback(topics.GET_IP_ADDRESS, None)
        await update.message.reply_text("Getting IP address...")
        return ConversationHandler.END
    
    async def __cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__bot_context = context
        return ConversationHandler.END
    
    async def __send_scheduled_message(self, context: ContextTypes.DEFAULT_TYPE):
        job = context.job
        await context.bot.send_message(job.chat_id, text=job.data)

    def send_message(self, message):
        job_queue = self.__app.job_queue
        job_queue.run_once(self.__send_scheduled_message, when=1, data=message, chat_id=self.__chat_id, name=f'send-message-{random.randint(0, 1000)}')

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