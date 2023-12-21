from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import logging
import validators
import topics
import random
import json
from dbaccess import MongoDbAccess

class TlBot:

    YOUTUBE_DOWNLOAD = 0
    POWER_STATE_SELECTOR = 1
    POWER_STATE_AFTER_SELECT = 2

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
    
    async def __power_the_device(self, update: Update, context: CallbackContext):
        self.__bot_context = context
        logging.info("got power request")
        args = context.args
        if len(args) == 2:
            device_name = args[0]
            state = True if args[1].lower() == 'on' else False
            payload = {
                "device_name": device_name,
                "state": state
            }
            self.__publish_callback(topics.DEVICE_TOGGLE, json.dumps(payload))
            await update.message.reply_text(f"Device {device_name} set to {state}")
            return ConversationHandler.END

        keyboard = [[]]
        with MongoDbAccess() as mongo_client:
            for device in mongo_client.get_devices_names():
                device_name = device[mongo_client.DEVICE_NAME_FIELD]
                keyboard[0].append(InlineKeyboardButton(device_name, callback_data=device_name))

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text="Choose device", reply_markup=reply_markup
        )
        return self.POWER_STATE_SELECTOR
    
    async def __power_select_device_state(self, update: Update, context: CallbackContext):
        logging.info('got device state request')
        query = update.callback_query
        await query.answer()
        
        device_name = query.data

        json_data_on = json.dumps({"device_name": device_name, "state": True})
        json_data_off = json.dumps({"device_name": device_name, "state": False})

        keyboard = [
            [
                InlineKeyboardButton("On", callback_data=json_data_on),
                InlineKeyboardButton("Off", callback_data=json_data_off),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"Choose a state for {device_name}", reply_markup=reply_markup
        )
        return self.POWER_STATE_AFTER_SELECT
    
    async def __power_after_state_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.info('got device after state select request')
        
        query = update.callback_query
        await query.answer()

        json_data = update.callback_query.data
        self.__publish_callback(topics.DEVICE_TOGGLE, json_data)

        await query.edit_message_text('Device toggled')

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
                CommandHandler("ipaddress", self.__get_ip_address, filters=filters.Chat(self.__chat_id)),
                CommandHandler("power", self.__power_the_device, filters=filters.Chat(self.__chat_id))
            ],
            states={
                self.YOUTUBE_DOWNLOAD: [MessageHandler(filters=filters.TEXT, callback=self.__video_download)],
                self.POWER_STATE_SELECTOR: [CallbackQueryHandler(self.__power_select_device_state)],
                self.POWER_STATE_AFTER_SELECT: [CallbackQueryHandler(self.__power_after_state_select)]
            },
            fallbacks=[CommandHandler("cancel", self.__cancel)]
        )
        self.__app.add_handler(conversation_handler)
        self.__app.run_polling()