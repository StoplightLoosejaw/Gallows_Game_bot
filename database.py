import random
import re
import os
import psycopg2


text_file = open("/app/dicts/OZHEGOV.TXT", "r")
lines = text_file.readlines()
text_file.close()
text_file_eng = open("/app/dicts/dictionary.csv", "r")
lines_eng = text_file_eng.readlines()
text_file_eng.close()


class GallowsEngine:
    def __init__(self):
        DATABASE_URL = os.environ['DATABASE_URL']
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.cursor = self.conn.cursor()

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS CURRENT_GAME ( USER_ID text," \
                                                        " GALLOWS_WORD text," \
                                                        " GALLOWS_STATUS_WORD text," \
                                                        " DESCRIPTION text," \
                                                        " CHARS text, MISTAKES integer)"
        stmt_users = "CREATE TABLE IF NOT EXISTS ALL_USERS ( USER_ID text," \
                     " WINS integer, LOSSES integer,IMAGES_FLG integer, LANG_FLG integer )"

        self.cursor.execute(stmt)
        self.cursor.execute(stmt_users)
        self.conn.commit()

    def add_row_current_game(self, arcg_user_id, arcg_gallows_word,
                             arcg_gallows_status_word, arcg_description, arcg_chars, arcg_mistakes):
        stmt = "INSERT INTO CURRENT_GAME (USER_ID, GALLOWS_WORD," \
               "GALLOWS_STATUS_WORD,DESCRIPTION,CHARS, MISTAKES) VALUES (%s, %s, %s, %s, %s, %s)"
        args = (str(arcg_user_id), arcg_gallows_word,
                arcg_gallows_status_word, arcg_description, arcg_chars, str(arcg_mistakes), )
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def add_row_all_users(self, arau_user_id, arau_wins, arau_losses, arau_images_flg, arau_lang_flg):
        stmt = "INSERT INTO ALL_USERS (USER_ID, WINS," \
               "LOSSES, IMAGES_FLG, LANG_FLG) VALUES (%s, %s, %s, %s, %s)"
        args = (str(arau_user_id), str(arau_wins), str(arau_losses), str(arau_images_flg), str(arau_lang_flg))
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def delete_row(self, dr_table_name, dr_user_id):
        stmt = "DELETE FROM {} WHERE USER_ID =  %s".format(dr_table_name)
        args = (str(dr_user_id), )
        self.cursor.execute(stmt, args)
        self.conn.commit()

    def update_field(self, uf_table_name, uf_field_name, uf_field_value, uf_user_id):
        if uf_field_name in ('WINS', 'LOSSES', 'IMAGES_FLG', 'LANG_FLG', 'MISTAKES'):
            stmt = "UPDATE {} SET {} = {} WHERE USER_ID = '{}'".format(uf_table_name, uf_field_name,
                                                                       uf_field_value, uf_user_id)
        else:
            stmt = "UPDATE {} SET {} = '{}' WHERE USER_ID = '{}'".format(uf_table_name, uf_field_name,
                                                                         uf_field_value, uf_user_id)
        self.cursor.execute(stmt)
        self.conn.commit()

    def get_items(self, gi_table_name, gi_field_name, gi_user_id):
        stmt = "SELECT {} FROM {} WHERE USER_ID = '{}'".format(gi_field_name, gi_table_name, gi_user_id)
        self.cursor.execute(stmt)
        try:
            return self.cursor.fetchone()[0]
        except TypeError:
            return False

    def new_player(self, np_user_id):
        self.add_row_all_users(np_user_id, 0, 0, 1, 1)

    def new_game(self, ng_user_id, ng_gallows_word, ng_description, ng_gallows_status_word):
        self.delete_row('CURRENT_GAME', ng_user_id)
        self.add_row_current_game(ng_user_id, ng_gallows_word,
                                  ng_gallows_status_word, ng_description, '', 0)

    def player_wins(self, pw_user_id):
        pw_word = self.get_items('CURRENT_GAME', 'GALLOWS_WORD', pw_user_id)
        self.delete_row('CURRENT_GAME', pw_user_id)
        new_wins = self.get_items('ALL_USERS', 'WINS', pw_user_id)+1
        self.update_field('ALL_USERS', 'WINS', new_wins, pw_user_id)
        return pw_word

    def player_loses(self, pw_user_id):
        pw_word = self.get_items('CURRENT_GAME', 'GALLOWS_WORD', pw_user_id)
        self.delete_row('CURRENT_GAME', pw_user_id)
        new_losses = self.get_items('ALL_USERS', 'LOSSES', pw_user_id)+1
        self.update_field('ALL_USERS', 'LOSSES', new_losses, pw_user_id)
        return pw_word

    def game_begin(self, gb_user_id):
        gb_gallows_word = 'PH'
        gb_description = 'PH'
        global lines, lines_eng
        if not self.get_items('ALL_USERS', 'USER_ID', gb_user_id):
            self.new_player(gb_user_id)
        gb_lang = self.get_items('ALL_USERS', 'LANG_FLG', gb_user_id)
        while len(gb_gallows_word) < 5:
            index = random.randint(0, len(lines))
            if gb_lang == 0:
                gb_gallows_word = lines[index].split('|')[0].strip().upper()
                gb_description = lines[index].split('|')[5].strip().upper()
            else:
                gb_gallows_word = lines_eng[index].split(',')[0].strip().upper()
                gb_gallows_word = re.sub('"', '', gb_gallows_word)
                gb_description = lines_eng[index].split(',')[-1].strip().upper()
                gb_description = re.sub('"', '', gb_description)
        gb_gallows_status_word = '_'*len(gb_gallows_word)
        self.new_game(gb_user_id, gb_gallows_word, gb_description, gb_gallows_status_word)
        return gb_gallows_word, gb_gallows_status_word

    def gallows_check(self, gc_inputchar, gc_user_id):
        gc_gallows_word = self.get_items('CURRENT_GAME', 'GALLOWS_WORD', gc_user_id)
        gc_gallows_status_word = list(self.get_items('CURRENT_GAME', 'GALLOWS_STATUS_WORD', gc_user_id))
        gc_mistakes = self.get_items('CURRENT_GAME', 'MISTAKES', gc_user_id)
        gc_inputchar = gc_inputchar.upper()
        if gc_inputchar in list(gc_gallows_word):
            kol = list(gc_gallows_word).count(gc_inputchar)
            indexes = []
            lastfound = 0
            for i in range(0, kol):
                index = list(gc_gallows_word).index(gc_inputchar, lastfound)
                indexes.append(index)
                lastfound = index+1
            for ind in indexes:
                gc_gallows_status_word[ind] = gc_inputchar
        else:
            gc_mistakes = gc_mistakes+1
        self.update_field('CURRENT_GAME', 'GALLOWS_STATUS_WORD', ''.join(gc_gallows_status_word), gc_user_id)
        self.update_field('CURRENT_GAME', 'MISTAKES', gc_mistakes, gc_user_id)
        gc_chars = self.update_chars(gc_inputchar, gc_user_id)
        return gc_gallows_status_word, gc_mistakes, gc_chars

    def update_chars(self, uc_input_char, uc_user_id):
        uc_chars = self.get_items('CURRENT_GAME', 'CHARS', uc_user_id)
        if uc_input_char not in uc_chars:
            uc_chars = uc_chars+uc_input_char
        self.update_field('CURRENT_GAME', 'CHARS', uc_chars, uc_user_id)
        return uc_chars

    def text_constants(self, tc_user_id):
        if not self.get_items('ALL_USERS', 'USER_ID',  tc_user_id) \
                or not self.get_items('CURRENT_GAME', 'USER_ID',  tc_user_id):
            lang = 0
            tc_gallows_status_word = list('PLACEHOLDER')
            tc_gallows_word = 'PLACEHOLDER'
            tc_mistakes = 0
            tc_wins = 0
            tc_losses = 0
            tc_chars = list('PLACEHOLDER')
        else:
            lang = self.get_items('ALL_USERS', 'LANG_FLG', tc_user_id)
            tc_gallows_status_word = list(self.get_items('CURRENT_GAME',
                                                         'GALLOWS_STATUS_WORD', tc_user_id))
            tc_gallows_word = self.get_items('CURRENT_GAME', 'GALLOWS_WORD', tc_user_id)
            tc_mistakes = self.get_items('CURRENT_GAME', 'MISTAKES', tc_user_id)
            tc_chars = list(self.get_items('CURRENT_GAME', 'CHARS', tc_user_id))
            tc_wins = self.get_items('ALL_USERS', 'WINS', tc_user_id)
            tc_losses = self.get_items('ALL_USERS', 'LOSSES', tc_user_id)
        if lang == 0:
            return{'win_text': "{}. Поздравляю с победой![any key чтобы начать заново]".format(
                                             tc_gallows_word),
                   'loss_text': "Попытки кончились!\n "
                                "Твое слово было {} [any key чтобы начать заново]".format(tc_gallows_word),
                   'turn_text':  "Твое слово\n {} \n Количество оставшихся попыток: {} \n Опробовано {}"
                                 .format(' '.join(tc_gallows_status_word),
                                         7 - tc_mistakes, ' '.join(list(tc_chars))),
                   'session_error_text': "Сессия оборвалась /start чтобы начать сначала",
                   'wrong_input': "Принимается только кириллица",
                   'commands_txt': "Команды: /toggle_img - вкл/выкл картинки \n "
                                   "/start - новая катка \n /my_stats - статистика" 
                                   " \n /info - все команды \n /hint - подсказка \n /toggle_lang - переключение языка",
                   'start_text_1': "Я хочу сыграть с тобой в игру",
                   'start_text_2': "Твое слово \n{}"
                                   "\n Количество оставшихся попыток: {}".format(' '.join(tc_gallows_status_word), 7),
                   'stats_text': "Побед: {} Поражений {}".format(int(tc_wins), int(tc_losses)),
                   'stats_error': "Хммм, походу либо вы новый игрок, либо данные потеряны навсегда",
                   'pics_off': "Картинки выключены! Чтобы их включить /toggle_img",
                   'pics_on': "Картинки включены! Чтобы их выключить /toggle_img",
                   'input_error_1': "За один раз только одна буква",
                   'input_error_2': "Эта буква уже была. Давай что-нибудь другое",
                   'lang': "Теперь все на русском. Игра начнется заново",
                   'hint_deny': "Слишком рано! Подсказку можно просить только если число ошибок больше трех"
                   }
        else:
            return {'win_text': "{}. Victory![any key to continue]".format(
                tc_gallows_word),
                'loss_text': "No attempts left!\n "
                             "Your word was {} [any key to continue]".format(tc_gallows_word),
                'turn_text': "Your word is \n {} \n Attempts left: {} \n You've already tried {}"
                .format(' '.join(tc_gallows_status_word),
                        7 - tc_mistakes, ' '.join(list(tc_chars))),
                'session_error_text': "Session abruptly ended /start to start again",
                'wrong_input': "Only latin alphabet is accepted",
                'commands_txt': "Commands: /toggle_img\n "
                                "/start\n /my_stats"
                                " \n /info \n /hint \n /toggle_lang",
                'start_text_1': "I want to play a game",
                'start_text_2': "Your word \n{}"
                                "\n Attempts left: {}".format(' '.join(tc_gallows_status_word), 7),
                'stats_text': "Wins: {} Losses {}".format(int(tc_wins), int(tc_losses)),
                'stats_error': "Hmm it looks like your data is lost forever",
                'pics_off': "Pictures are switched off! To switch them on /toggle_img",
                'pics_on': "Pictures are switched on! To switch them off /toggle_img",
                'input_error_1': "Only one letter at a time",
                'input_error_2': "You've already tried this. Try something different",
                'lang': "Everything is in english now. The game will start again",
                'hint_deny': "Too early! You can ask for the hint only after five  failed attempts "
            }
