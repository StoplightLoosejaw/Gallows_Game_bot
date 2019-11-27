import telebot
from telebot import apihelper
from database import GallowsEngine

apihelper.proxy = {proxy}
bot = telebot.TeleBot(token)

commands_message = "Команды: /toggle_img - вкл/выкл картинки \n /start - новая катка \n /my_stats - статистика" \
                 " \n /info - все команды \n /hint - подсказка"
db = GallowsEngine()
db.setup()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not db.get_items('ALL_USERS', 'WINS', message.from_user.id):
        bot.reply_to(message, commands_message)
    db.game_begin(message.from_user.id)
    s_flag = db.get_items('ALL_USERS', 'IMAGES_FLG', message.from_user.id)
    bot.reply_to(message, "Я хочу сыграть с тобой в игру")
    if s_flag == 1:
        bot.send_photo(message.from_user.id, photo='https://i.ytimg.com/vi/PkWw1gX6xDk/maxresdefault.jpg')
    s_gallows_status_word = list(db.get_items('CURRENT_GAME', 'GALLOWS_STATUS_WORD', message.from_user.id))
    bot.send_message(message.from_user.id,
                     "Твое слово \n{}"
                     "\n Количество оставшихся попыток: {}".format(' '.join(s_gallows_status_word), 7))


@bot.message_handler(commands=['my_stats'])
def my_stats(message):
    try:
        ms_wins = db.get_items('ALL_USERS', 'WINS', message.from_user.id)
        ms_losses = db.get_items('ALL_USERS', 'LOSSES', message.from_user.id)
        bot.reply_to(message, "Побед: {} Поражений {}".format(int(ms_wins), int(ms_losses)))
    except:
        bot.reply_to(message, "Хммм, походу либо вы новый игрок, либо данные потеряны навсегда")


@bot.message_handler(commands=['hint'])
def hint(message):
    m_description = db.get_items('CURRENT_GAME', 'DESCRIPTION', message.from_user.id)
    m_mistakes = db.get_items('CURRENT_GAME', 'MISTAKES', message.from_user.id)
    if m_mistakes > 3:
        bot.reply_to(message, m_description)
    else:
        bot.reply_to(message, "Слишком рано! Подсказку можно просить только если число ошибок больше трех")


@ bot.message_handler(commands=['cheat'])
def cheat(message):
    c_gallows_word = db.get_items('CURRENT_GAME', 'GALLOWS_WORD', message.from_user.id)
    bot.reply_to(message, c_gallows_word)


@ bot.message_handler(commands=['info'])
def info(message):
    bot.reply_to(message, commands_message)


@ bot.message_handler(commands=['toggle_img'])
def toggle(message):
    s_flag = db.get_items('ALL_USERS', 'IMAGES_FLG', message.from_user.id)
    if s_flag == 1:
        db.update_field('ALL_USERS', 'IMAGES_FLG', 0,  message.from_user.id)
        bot.reply_to(message, "Картинки выключены! Чтобы их включить /toggle_img")
    if s_flag == 0:
        db.update_field('ALL_USERS', 'IMAGES_FLG', 1,  message.from_user.id)
        bot.reply_to(message, "Картинки включены! Чтобы их выключить /toggle_img")


@bot.message_handler(regexp="[А-ЯёЁ-]")
def meat(message):
    if db.get_items('CURRENT_GAME', 'GALLOWS_WORD', message.from_user.id):
        m_gallows_word = db.get_items('CURRENT_GAME', 'GALLOWS_WORD', message.from_user.id)
        m_gallows_status_word = db.get_items('CURRENT_GAME', 'GALLOWS_STATUS_WORD', message.from_user.id)
        m_mistakes = db.get_items('CURRENT_GAME', 'MISTAKES', message.from_user.id)
        m_chars = db.get_items('CURRENT_GAME', 'CHARS', message.from_user.id)
        if 7-m_mistakes > 0 and '_' in m_gallows_status_word:
            if len(message.text) > 1 and message.text.upper() != m_gallows_word:
                bot.send_message(message.from_user.id, "За один раз только одна буква")
            elif message.text.upper() in m_chars:
                bot.send_message(message.from_user.id, "Эта буква уже была. Давай что-нибудь другое")
            else:
                if message.text.upper() == m_gallows_word:
                    db.player_wins(message.from_user.id)
                    bot.send_message(message.from_user.id,
                                     "{}. Поздравляю с победой![any key чтобы начать заново]".format(m_gallows_word))
                    bot.register_next_step_handler(message, send_welcome)
                else:
                    db.gallows_check(message.text, message.from_user.id)
                    m_gallows_status_word = list(db.get_items('CURRENT_GAME',
                                                              'GALLOWS_STATUS_WORD', message.from_user.id))
                    m_gallows_word = db.get_items('CURRENT_GAME', 'GALLOWS_WORD', message.from_user.id)
                    m_mistakes = db.get_items('CURRENT_GAME', 'MISTAKES', message.from_user.id)
                    m_flag = db.get_items('ALL_USERS', 'IMAGES_FLG', message.from_user.id)
                    m_chars = list(db.get_items('CURRENT_GAME', 'CHARS', message.from_user.id))
                    if m_flag == 1:
                        bot.send_photo(message.from_user.id,
                                       photo=open('telegrambot/{}.png'.format(m_mistakes), 'rb'))
                    bot.reply_to(message, "Твое слово\n {} \n Количество оставшихся попыток: {} \n Опробовано {}"
                                 .format(' '.join(m_gallows_status_word), 7 - m_mistakes, ' '.join(list(set(m_chars)))))
                    if 7-m_mistakes == 0:
                        db.player_loses(message.from_user.id)
                        bot.send_message(message.from_user.id,
                                         "Попытки кончились!\n "
                                         "Твое слово было {} [any key чтобы начать заново]".format(m_gallows_word))
                        bot.register_next_step_handler(message, send_welcome)
                    if '_' not in m_gallows_status_word:
                        db.player_wins(message.from_user.id)
                        bot.send_message(message.from_user.id,
                                         "{}. Поздравляю с победой![any key чтобы начать заново]".format(
                                             m_gallows_word))
                        bot.register_next_step_handler(message, send_welcome)
    else:
        bot.send_message(message.from_user.id, "Сессия оборвалась /start чтобы начать сначала")


@bot.message_handler(regexp="[^А-ЯёЁ-]")
def echo_all(message):
    bot.reply_to(message, "Принимается только кириллица")


bot.polling(none_stop=True)
