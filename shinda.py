from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from tinydb import TinyDB, Query
import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

botId = # ..
chatId = # ..
sudoUsers = []

def help(bot, update):
    update.message.reply_text('Hello. You\'re cant use that command, sorry.')

def botWarn(bot, update):
	replyMessage = update.message.reply_to_message

	if None == replyMessage:
		return
	
	if botId == replyMessage.from_user.id:
		bot.sendMessage(update.message.chat_id, 'Вы не можете пожаловаться на меня')
	
		return

	if None == replyMessage:
		bot.sendMessage(update.message.chat_id, 'Вы должны выбрать сообщение с нарушением')
	else:
		for admin in bot.get_chat_administrators(chatId):
			if botId != admin.user.id:
				if admin.user.id == update.message.from_user.id:
					return warnUser(bot, update)
				else:
					bot.sendMessage(admin.user.id, 'В чате нарушитель. Его айди: {}. Его профиль @{}. Его имя и фамилия: {} | {}. Его сообщение: {}'
								.format(replyMessage.from_user.id, replyMessage.from_user.username,
										replyMessage.from_user.first_name, 
										replyMessage.from_user.last_name, replyMessage.text))

def warnUser(bot, update):
	userId = update.message.reply_to_message.from_user.id
	db = TinyDB('user_warns.json')
	User = Query()
	userInDb = db.get(User.user_id == userId)

	if None == userInDb:
		db.insert({'user_id': userId, 'username': update.message.reply_to_message.from_user.username, 'count': 1});
		
		bot.sendMessage(chatId, u'Предупрежден: 1/2', reply_to_message_id = update.message.reply_to_message.message_id)
	else:
		db.update({'count': 2}, User.user_id == userId)

		# bot.restrictChatMember(chatId, update.message.reply_to_message.from_user.id)
		bot.restrictChatMember(chatId, userId)

		bot.kickChatMember(chat_id = chatId, user_id = userId)

		bot.sendMessage(chatId, u'Пользователь заблокирован', reply_to_message_id = update.message.reply_to_message.message_id)

def unbanUser(bot, update, args):
	if False == isAdmin(bot, update.message.from_user.id):
		return

	dbWarns = TinyDB('user_warns.json')
	dbBans = TinyDB('users_in_ban.json')
	User = Query()
	userId = update.message.reply_to_message.from_user.id if 0 == len(args) else int(args[0])
	sender = chatId if 'supergroup' == update.message.chat.type else update.message.from_user.id
	wasInBan = False

	if botId == userId:
		bot.sendMessage(sender, 'Простите, я не могу быть в бане')

	if 0 != len(dbWarns.search(User.user_id == userId)):
		dbWarns.remove(User.user_id == userId)
		wasInBan = True
	else:
		wasInBan = False

	if 0 != len(dbBans.search(User.user_id == userId)):
		dbBans.remove(User.user_id == userId)
		wasInBan = True
	else:
		wasInBan = False if False == wasInBan else True

	if False == wasInBan:
		bot.sendMessage(sender, 'Пользователь не заблокирован')

		return

	bot.unbanChatMember(chatId, userId)

	bot.sendMessage(sender, 'Пользователь успешно разблокирован')

def banUser(bot, update, args):
	if False == isAdmin(bot, update.message.from_user.id):
		return

	if 'supergroup' == update.message.chat.type:
		return banUserGroup(bot, update, args)
	else:
		return banUserPm(bot, update, args)

def banUserGroup(bot, update, args):
	replyMessage = update.message.reply_to_message

	if None == replyMessage:
		bot.sendMessage(chatId, 'Эй, Вы должны ответить на сообщение')

		return

	if update.message.from_user.id == replyMessage.from_user.id:
		bot.sendMessage(chatId, 'Не стоит этого делать')

		return

	if replyMessage.from_user.id == botId:
		bot.sendMessage(chatId, 'Неа, не пройдет :)')

		return

	db = TinyDB('users_in_ban.json')
	User = Query()
	userInBan = db.get(User.user_id == replyMessage.from_user.id)
	daysForBan = 1 if 0 == len(args) else args[0]

	if None == userInBan:
		db.insert({'user_id': replyMessage.from_user.id, 'username': replyMessage.from_user.username, 'unban_date': daysForBan})
	else:
		bot.sendMessage(chatId, 'Пользователь заблокирован на {} дней'.format(userInBan['unban_date']))

		return

	bot.restrictChatMember(chatId, replyMessage.from_user.id, daysForBan, False, False, False, False)

	bot.kickChatMember(chat_id = chatId, user_id = replyMessage.from_user.id)

	bot.sendMessage(chatId, u'Пользователь @{} был заблокирован на {} дней'.format(
					replyMessage.from_user.username, args[0]))

def banUserPm(bot, update, args):
	isAdmin = False
	sender = update.message.from_user.id

	if 0 == len(args):
		return

	banUserId = args[0]
	db = TinyDB('users_in_ban.json')
	User = Query()
	daysForBan = 1 if 0 == len(args) else args[0]

	if None == db.get(User.user_id == args[0]):
		db.insert({'user_id': args[0], 'username': '', 'unban_date': daysForBan})
	else:
		bot.sendMessage(update.message.from_user.id, 'Пользователь заблокирован на {} дней'.format(userInBan['unban_date']))

		return

	bot.restrictChatMember(chatId, banUserId, daysForBan, False, False, False, False)

	bot.kickChatMember(chat_id = chatId, user_id = banUserId)

	bot.sendMessage(update.message.from_user.id, 'Success')

def kickUser(bot, update, args):
	if False == isAdmin(bot, update.message.from_user.id):
		return
	
	userId = int(args[0]) if 0 != len(args) else update.message.reply_to_message.from_user.id
	sendTo = chatId if 'supergroup' == update.message.chat.type else update.message.from_user.id

	if botId == userId:
		bot.sendMessage(sendTo, 'Прекрати, пожалуйста')

		return

	if 0 == len(args):
		bot.kickChatMember(chat_id = chatId, user_id = userId)
	else:
		bot.kickChatMember(chat_id = chatId, user_id = userId)

def muteUser(bot, update, args):
	if False == isAdmin(bot, update.message.from_user.id):
		return

	sendTo = chatId if 'supergroup' == update.message.chat.type else update.message.from_user.id
	
	if 0 == len(args) and None == update.message.reply_to_message:
		bot.sendMessage(sendTo, 'Эй, Вы должны ответить на сообщение')

		return

	db = TinyDB('users_in_mute.json')
	User = Query()
	userId = update.message.reply_to_message.from_user.id if 0 == len(args) else int(args[0])
	userInMute = db.get(User.user_id == userId)
	wasInMute = False

	if botId == userId:
		bot.sendMessage(sendTo, 'Я хороший')

		return

	if 0 == len(args) and None == update.message.reply_to_message:
		bot.sendMessage(sendTo, 'Эй, Вы должны ответить на сообщение')

		return

	if 0 == len(args):
		if None == userInMute:
			bot.restrictChatMember(chatId, update.message.reply_to_message.from_user.id, 366, False, False, False, False)

			db.insert({'user_id': update.message.reply_to_message.from_user.id})
		else:
			wasInMute = True
	else:
		if None == userInMute:
			bot.restrictChatMember(chatId, userId, 366, False, False, False, False)

			db.insert({'user_id': userId})
		else:
			wasInMute = True

	bot.sendMessage(sendTo, 'Пользователь больше не сможет писать' if wasInMute == False else 'Пользователь уже в муте')

def unmuteUser(bot, update, args):
	if False == isAdmin(bot, update.message.from_user.id):
		return

	sendTo = chatId if 'supergroup' == update.message.chat.type else update.message.from_user.id

	if 0 == len(args) and None == update.message.reply_to_message:
		bot.sendMessage(sendTo, 'Эй, Вы должны ответить на сообщение')

		return
	
	db = TinyDB('users_in_mute.json')
	User = Query()
	userId = update.message.reply_to_message.from_user.id if 0 == len(args) else int(args[0])
	userInMute = db.get(User.user_id == userId)

	if botId == userId:
		return

	if None == userInMute:
		bot.sendMessage(sendTo, 'Пользователь может писать')

		return
	else:
		db.remove(User.user_id == userId)

		bot.restrictChatMember(chatId, userId, 366, True, True, True, True)

		bot.sendMessage(sendTo, 'Теперь пользователь сможет нарушать')

def isAdmin(bot, userId):
	isAdmin = False

	for admin in bot.get_chat_administrators(chatId):
		if admin.user.id != userId:
			isAdmin = False
		else:
			isAdmin = True

	return isAdmin

def addAdmin(bot, update, args):
	if update.message.from_user.id != sudoUsers[0] and update.message.from_user.id != sudoUsers[1]:
		return

	if 0 == len(args) and None == update.message.reply_to_message:
		return

	userId = update.message.reply_to_message.from_user.id if 0 == len(args) else int(args[0])
	db = TinyDB('admins.json')
	User = Query()

	if None != db.get(User.user_id == userId):
		return

	db.insert({'user_id': userId})

	bot.promoteChatMember(chatId, userId, True, False, False, True, False, True, True, False)

def removeAdmin(bot, update, args):
	if update.message.from_user.id != sudoUsers[0] and update.message.from_user.id != sudoUsers[1]:
		return

	if 0 == len(args) and None == update.message.reply_to_message:
		return
	
	userId = update.message.reply_to_message.from_user.id if 0 == len(args) else int(args[0])
	db = TinyDB('admins.json')
	User = Query()

	if None == db.get(User.user_id == userId):
		return

	db.remove(User.user_id == userId)

	bot.promoteChatMember(chatId, userId, False, False, False, False, False, False, False, False)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    updater = Updater('Bot token')

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('warn', botWarn))
    dp.add_handler(CommandHandler('ban', banUser, pass_args = True))
    dp.add_handler(CommandHandler('unban', unbanUser, pass_args = True))
    dp.add_handler(CommandHandler('kick', kickUser, pass_args = True))
    dp.add_handler(CommandHandler('mute', muteUser, pass_args = True))
    dp.add_handler(CommandHandler('unmute', unmuteUser, pass_args = True))
    dp.add_handler(CommandHandler('addAdmin', addAdmin, pass_args = True))
    dp.add_handler(CommandHandler('removeAdmin', removeAdmin, pass_args = True))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
