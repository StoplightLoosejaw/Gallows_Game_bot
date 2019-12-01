import telebot
import re
import os
#from telebot import apihelper
from database import GallowsEngine

#apihelper.proxy = {'https': 'socks5h://149.28.35.94:1080'}
bot = telebot.TeleBot(os.getenv("TOKEN"))

db = GallowsEngine()
db.setup()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not db.get_items('ALL_USERS', 'USER_ID', message.from_user.id):
        bot.reply_to(message, db.text_constants(message.from_user.id)['commands_txt'])
    db.game_begin(message.from_user.id)
    s_flag = db.get_items('ALL_USERS', 'IMAGES_FLG', message.from_user.id)
    bot.reply_to(message, db.text_constants(message.from_user.id)['start_text_1'])
    if s_flag == 1:
        bot.send_photo(message.from_user.id, photo='https://i.ytimg.com/vi/PkWw1gX6xDk/maxresdefault.jpg')
    bot.send_message(message.from_user.id,  db.text_constants(message.from_user.id)['start_text_2'])


@bot.message_handler(commands=['my_stats'])
def my_stats(message):
    try:
        bot.reply_to(message, db.text_constants(message.from_user.id)['stats_text'])
    except:
        bot.reply_to(message, db.text_constants(message.from_user.id)['stats_error'])


@bot.message_handler(commands=['hint'])
def hint(message):
    m_description = db.get_items('CURRENT_GAME', 'DESCRIPTION', message.from_user.id)
    m_mistakes = db.get_items('CURRENT_GAME', 'MISTAKES', message.from_user.id)
    if m_mistakes > 3:
        bot.reply_to(message, m_description)
    else:
        bot.reply_to(message, db.text_constants(message.from_user.id)['hint_deny'])


@ bot.message_handler(commands=['cheat'])
def cheat(message):
    c_gallows_word = db.get_items('CURRENT_GAME', 'GALLOWS_WORD', message.from_user.id)
    bot.reply_to(message, c_gallows_word)


@ bot.message_handler(commands=['info'])
def info(message):
    bot.reply_to(message, db.text_constants(message.from_user.id)['commands_txt'])


@ bot.message_handler(commands=['toggle_img'])
def toggle(message):
    s_flag = db.get_items('ALL_USERS', 'IMAGES_FLG', message.from_user.id)
    if s_flag == 1:
        db.update_field('ALL_USERS', 'IMAGES_FLG', 0,  message.from_user.id)
        bot.reply_to(message, db.text_constants(message.from_user.id)['pics_off'])
    if s_flag == 0:
        db.update_field('ALL_USERS', 'IMAGES_FLG', 1,  message.from_user.id)
        bot.reply_to(message, db.text_constants(message.from_user.id)['pics_on'])


@ bot.message_handler(commands=['toggle_lang'])
def toggle(message):
    l_flag = db.get_items('ALL_USERS', 'LANG_FLG', message.from_user.id)
    if l_flag == 1:
        db.update_field('ALL_USERS', 'LANG_FLG ', 0,  message.from_user.id)
        bot.reply_to(message, db.text_constants(message.from_user.id)['lang'])
        bot.register_next_step_handler(message, send_welcome)
    if l_flag == 0:
        db.update_field('ALL_USERS', 'LANG_FLG', 1,  message.from_user.id)
        bot.reply_to(message, db.text_constants(message.from_user.id)['lang'])
        bot.register_next_step_handler(message, send_welcome)


@bot.message_handler()
def meat(message):
    m_flag = db.get_items('ALL_USERS', 'LANG_FLG', message.from_user.id)
    if m_flag == 0:
        regexp = "[а-яА-ЯёЁ-]"
    else:
        regexp = "[a-zA-Z-]"
    if re.match(regexp, message.text):
        if db.get_items('CURRENT_GAME', 'GALLOWS_WORD', message.from_user.id):
            m_gallows_word = db.get_items('CURRENT_GAME', 'GALLOWS_WORD', message.from_user.id)
            m_gallows_status_word = db.get_items('CURRENT_GAME', 'GALLOWS_STATUS_WORD', message.from_user.id)
            m_mistakes = db.get_items('CURRENT_GAME', 'MISTAKES', message.from_user.id)
            m_chars = db.get_items('CURRENT_GAME', 'CHARS', message.from_user.id)
            if 7-m_mistakes > 0 and '_' in m_gallows_status_word:
                if len(message.text) > 1 and message.text.upper() != m_gallows_word:
                    bot.send_message(message.from_user.id, db.text_constants(message.from_user.id)['input_error_1'])
                elif message.text.upper() in m_chars:
                    bot.send_message(message.from_user.id, db.text_constants(message.from_user.id)['input_error_2'])
                else:
                    if message.text.upper() == m_gallows_word:
                        bot.send_message(message.from_user.id, db.text_constants(message.from_user.id)['win_text'])
                        db.player_wins(message.from_user.id)
                        bot.register_next_step_handler(message, send_welcome)
                    else:
                        db.gallows_check(message.text, message.from_user.id)
                        m_gallows_status_word = list(db.get_items('CURRENT_GAME',
                                                                  'GALLOWS_STATUS_WORD', message.from_user.id))
                        m_mistakes = db.get_items('CURRENT_GAME', 'MISTAKES', message.from_user.id)
                        m_flag = db.get_items('ALL_USERS', 'IMAGES_FLG', message.from_user.id)
                        if m_flag == 1:
                            bot.send_photo(message.from_user.id,
                                           photo=open('https://github.com/StoplightLoosejaw/Gallows_Game_bot/raw/master/pics/{}.png'.format(m_mistakes), 'rb'))
                        bot.reply_to(message, db.text_constants(message.from_user.id)['turn_text'])
                        if 7-m_mistakes == 0:
                            bot.send_message(message.from_user.id, db.text_constants(message.from_user.id)['loss_text'])
                            db.player_loses(message.from_user.id)
                            bot.register_next_step_handler(message, send_welcome)
                        if '_' not in m_gallows_status_word:
                            bot.send_message(message.from_user.id, db.text_constants(message.from_user.id)['win_text'])
                            db.player_wins(message.from_user.id)
                            bot.register_next_step_handler(message, send_welcome)
        else:
            bot.send_message(message.from_user.id, db.text_constants(message.from_user.id)['session_error_text'])
    else:
        bot.reply_to(message, db.text_constants(message.from_user.id)['wrong_input'])


bot.polling(none_stop=True)
