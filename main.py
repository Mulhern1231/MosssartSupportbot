from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from config import TOKEN

ADMINS = [426156432]
pending_answers = {}

def start(update: Update, context):
    welcome_message = (
        "Привет! 👋🏻\n"
        "Ты пишешь в отдел заботы онлайн-обучения Насти Mosssart. Наша миссия — сделать твоё обучение "
        "максимально комфортным и понятным.\n\n"
        "💌 C чем мы можем тебе помочь?\n\n"
        "1. Ответить на все твои вопросы касательно курса.\n"
        "2. Помочь в случае возникновения технических проблем.\n\n"
        "Если возникнут вопросы — не стесняйся обращаться. Мы здесь, чтобы помогать! 🫂"
    )
    update.message.reply_text(welcome_message)


def forward_to_admins(update, context, user_id, user_name):
    # Создаем кнопку для ответа
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ответить", callback_data=f"answer-{user_id}")]
    ])
    
    for admin_id in ADMINS:
        if update.message.text:
            context.bot.send_message(admin_id, f"Вопрос от {user_name} (ID: {user_id}):\n{update.message.text}", reply_markup=keyboard)
        else:
            context.bot.forward_message(admin_id, update.message.chat.id, update.message.message_id)
            context.bot.send_message(admin_id, f"Медиа от {user_name} (ID: {user_id}). Нажмите кнопку ниже, чтобы ответить:", reply_markup=keyboard)


def handle_message(update: Update, context):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    # Если это ответ от админа
    if user_id in ADMINS and user_id in pending_answers:
        user_id_to_reply = pending_answers[user_id]
        if update.message.text:
            context.bot.send_message(user_id_to_reply, f"{update.message.text}")
        else:
            context.bot.forward_message(user_id_to_reply, update.message.chat.id, update.message.message_id)
        update.message.reply_text("Ответ отправлен.")
        del pending_answers[user_id]
    # Если это новый вопрос от админа
    elif user_id in ADMINS:
        update.message.reply_text("Вы отправили сообщение без указания получателя. Если вы хотите ответить на вопрос, используйте кнопку 'Ответить'.")
    else:
        forward_to_admins(update, context, user_id, user_name)



def handle_callback(update: Update, context):
    query = update.callback_query
    if query.data.startswith("answer-"):
        user_id = int(query.data.split("-")[1])
        admin_name = query.from_user.first_name or "Админ"
        
        # Удаляем кнопку "Ответить" для всех админов
        query.edit_message_reply_markup(reply_markup=None)
        
        # Уведомляем других админов
        for admin_id in ADMINS:
            if admin_id != query.from_user.id:
                context.bot.send_message(admin_id, f"{admin_name} уже отвечает на вопрос от пользователя с ID {user_id}.")
        
        pending_answers[query.from_user.id] = user_id
        query.message.reply_text("Введите ваш ответ:")


def add_admin(update: Update, context):
    admin_id = update.message.from_user.id
    if admin_id in ADMINS:
        try:
            new_admin_id = int(context.args[0])
            ADMINS.append(new_admin_id)
            update.message.reply_text(f"Пользователь с ID {new_admin_id} добавлен в админы.")
        except (IndexError, ValueError):
            update.message.reply_text("Используйте: /addadmin <user_id>")
    else:
        update.message.reply_text("Вы не имеете прав на выполнение этой команды.")

def get_my_id(update: Update, context):
    user_id = update.message.from_user.id
    update.message.reply_text(f"Ваш ID: {user_id}")

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('addadmin', add_admin, pass_args=True))
    dp.add_handler(CommandHandler('myid', get_my_id))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command | Filters.photo | Filters.video | Filters.audio | Filters.voice, handle_message))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
