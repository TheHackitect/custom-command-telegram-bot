import logging
from sqlalchemy.orm import Session
from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

from config import BOT_TOKEN, ADMIN_ID
from models import SessionLocal, User, Admin, Command

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    ADD_COMMAND,
    ADD_DESCRIPTION,
    ADD_RESPONSE,
    ADD_IS_ADMIN,
    EDIT_COMMAND,
    EDIT_CHOICE,
    EDIT_DESCRIPTION,
    EDIT_RESPONSE,
    EDIT_IS_ADMIN,
    DELETE_COMMAND,
    DELETE_CONFIRMATION,
    ADD_ADMIN,
    DELETE_ADMIN_CONFIRMATION
) = range(13)

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db: Session = next(get_db())
    if not db.query(User).filter(User.telegram_id == user.id).first():
        new_user = User(telegram_id=user.id)
        db.add(new_user)
        db.commit()
    welcome_message = f"Hi {user.mention_html()}! "
    additional_message = db.query(Command).filter_by(command='start').first()
    if additional_message:
        welcome_message += f"\n\n{additional_message.response}"
        welcome_message += f"\n\nType /help to see available commands."
        markup = ReplyKeyboardMarkup([['🔙 Back_Start']], resize_keyboard=True)
    await update.message.reply_html(
        rf"{welcome_message}", reply_markup=markup, disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db: Session = next(get_db())
    commands = db.query(Command).filter_by(is_admin=False).all()
    help_text = "Available commands:\n"
    for cmd in commands:
        help_text += f"/{cmd.command}: {cmd.description}\n"
    await update.message.reply_text(help_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db: Session = next(get_db())
    commands = db.query(Command).filter_by(is_admin=False).all()
    help_text = "Available commands:\n\n"
    for cmd in commands:
        help_text += f"/{cmd.command}: {cmd.description}\n\n"
    await update.message.reply_text(help_text)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    command_text = update.message.text[1:]
    db: Session = next(get_db())
    command = db.query(Command).filter_by(command=command_text).first()

    if command:
        if command.is_admin and user.id != ADMIN_ID:
            await update.message.reply_text("This command is restricted to admins.")
        else:
            await update.message.reply_text(command.response)
    else:
        await update.message.reply_text("Command not found.")

# Conversation handlers for adding a command
async def add_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_id = update.effective_user.id
    db: Session = next(get_db())
    admin = db.query(Admin).filter_by(telegram_id=admin_id).first()
    if not admin:
        await update.message.reply_text("You are not authorized to perform this action.")
        return ConversationHandler.END
    await update.message.reply_text("Enter the command without '/':")
    return ADD_COMMAND

async def add_command_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    command = update.message.text
    context.user_data['command'] = (command.replace(' ','_')).lower()
    await update.message.reply_text("Enter the description:")
    return ADD_DESCRIPTION

async def add_command_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Enter the response:")
    return ADD_RESPONSE

async def add_command_is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['response'] = update.message.text
    await update.message.reply_text("Is this an admin command? (yes/no)")
    return ADD_IS_ADMIN

async def add_command_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    is_admin = update.message.text.lower() == 'yes'
    db: Session = next(get_db())
    new_command = Command(
        command=context.user_data['command'],
        description=context.user_data['description'],
        response=context.user_data['response'],
        is_admin=is_admin
    )
    db.add(new_command)
    db.commit()
    await update.message.reply_text(f"Command /{new_command.command} created successfully.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Conversation handlers for editing a command
async def edit_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_id = update.effective_user.id
    db: Session = next(get_db())
    admin = db.query(Admin).filter_by(telegram_id=admin_id).first()
    if not admin:
        await update.message.reply_text("You are not authorized to perform this action.")
        return ConversationHandler.END
    await update.message.reply_text("Enter the command you want to edit:")
    return EDIT_COMMAND

async def edit_command_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    command_text = update.message.text
    db: Session = next(get_db())
    command = db.query(Command).filter_by(command=command_text).first()
    if not command:
        await update.message.reply_text("Command not found.")
        return ConversationHandler.END
    context.user_data['command_id'] = command.id
    keyboard = [['Description', 'Response', 'Admin Status']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("What do you want to edit?", reply_markup=reply_markup)
    return EDIT_CHOICE

async def edit_command_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['edit_choice'] = 'description'
    await update.message.reply_text("Enter the new description:")
    return EDIT_DESCRIPTION

async def edit_command_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['edit_choice'] = 'response'
    await update.message.reply_text("Enter the new response:")
    return EDIT_RESPONSE

async def edit_command_is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['edit_choice'] = 'is_admin'
    await update.message.reply_text("Is this an admin command? (yes/no)")
    return EDIT_IS_ADMIN

async def edit_command_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db: Session = next(get_db())
    command = db.query(Command).filter_by(id=context.user_data['command_id']).first()
    edit_choice = context.user_data['edit_choice']
    if edit_choice == 'description':
        command.description = update.message.text
    elif edit_choice == 'response':
        command.response = update.message.text
    elif edit_choice == 'is_admin':
        command.is_admin = update.message.text.lower() == 'yes'
    db.commit()
    await update.message.reply_text("Command updated successfully.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Conversation handlers for deleting a command
async def delete_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_id = update.effective_user.id
    db: Session = next(get_db())
    admin = db.query(Admin).filter_by(telegram_id=admin_id).first()
    if not admin:
        await update.message.reply_text("You are not authorized to perform this action.")
        return ConversationHandler.END
    await update.message.reply_text("Enter the command you want to delete:")
    return DELETE_COMMAND

async def delete_command_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['command'] = update.message.text
    db: Session = next(get_db())
    command = db.query(Command).filter_by(command=context.user_data['command']).first()
    if not command:
        await update.message.reply_text("Command not found.")
        return ConversationHandler.END
    await update.message.reply_text(f"Are you sure you want to delete the command /{command.command}? (yes/no)")
    return DELETE_CONFIRMATION

async def delete_command_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'yes':
        db: Session = next(get_db())
        command = db.query(Command).filter_by(command=context.user_data['command']).first()
        db.delete(command)
        db.commit()
        await update.message.reply_text("Command deleted successfully.")
    else:
        await update.message.reply_text("Deletion cancelled.")
    return ConversationHandler.END

# Conversation handlers for adding and deleting admins
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_id = update.effective_user.id
    db: Session = next(get_db())
    admin = db.query(Admin).filter_by(telegram_id=admin_id).first()
    if not admin:
        await update.message.reply_text("You are not authorized to perform this action.")
        return ConversationHandler.END
    await update.message.reply_text("Enter the Telegram ID of the new admin:")
    return ADD_ADMIN

async def add_admin_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_admin_id = int(update.message.text)
    db: Session = next(get_db())
    new_admin = Admin(telegram_id=new_admin_id)
    db.add(new_admin)
    db.commit()
    await update.message.reply_text("New admin added successfully.")
    return ConversationHandler.END

async def delete_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_id = update.effective_user.id
    db: Session = next(get_db())
    admin = db.query(Admin).filter_by(telegram_id=admin_id).first()
    if not admin:
        await update.message.reply_text("You are not authorized to perform this action.")
        return ConversationHandler.END
    await update.message.reply_text("Enter the Telegram ID of the admin to delete:")
    return DELETE_ADMIN_CONFIRMATION

async def delete_admin_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_id = int(update.message.text)
    db: Session = next(get_db())
    admin = db.query(Admin).filter_by(telegram_id=admin_id).first()
    if admin:
        db.delete(admin)
        db.commit()
        await update.message.reply_text("Admin deleted successfully.")
    else:
        await update.message.reply_text("Admin not found.")
    return ConversationHandler.END

# Main function to start the bot
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex('🔙 Back_Start'), start))
    application.add_handler(CommandHandler("help", help_command))

    # Conversation handlers for adding commands
    add_command_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addcommand", add_command_start)],
        states={
            ADD_COMMAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_command_description)],
            ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_command_response)],
            ADD_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_command_is_admin)],
            ADD_IS_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_command_finish)],
        },
        fallbacks=[],
    )

    # Conversation handlers for editing commands
    edit_command_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("editcommand", edit_command_start)],
        states={
            EDIT_COMMAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_command_choice)],
            EDIT_CHOICE: [
                MessageHandler(filters.Regex('^(Description)$'), edit_command_description),
                MessageHandler(filters.Regex('^(Response)$'), edit_command_response),
                MessageHandler(filters.Regex('^(Admin Status)$'), edit_command_is_admin),
            ],
            EDIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_command_finish)],
            EDIT_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_command_finish)],
            EDIT_IS_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_command_finish)],
        },
        fallbacks=[],
    )

    # Conversation handlers for deleting commands
    delete_command_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("deletecommand", delete_command_start)],
        states={
            DELETE_COMMAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_command_confirmation)],
            DELETE_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_command_finish)],
        },
        fallbacks=[],
    )

    # Conversation handlers for managing admins
    add_admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addadmin", add_admin_start)],
        states={
            ADD_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_finish)],
        },
        fallbacks=[],
    )

    delete_admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("deleteadmin", delete_admin_start)],
        states={
            DELETE_ADMIN_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_admin_finish)],
        },
        fallbacks=[],
    )

    # Add conversation handlers to the application
    application.add_handler(add_command_conv_handler)
    application.add_handler(edit_command_conv_handler)
    application.add_handler(delete_command_conv_handler)
    application.add_handler(add_admin_conv_handler)
    application.add_handler(delete_admin_conv_handler)

    # Echo handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
