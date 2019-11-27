import sqlite3
import random

text_file = open("OZHEGOV.txt", "r")
lines = text_file.readlines()
text_file.close()


class GallowsEngine:
    def __init__(self, db_name="gallows_db.sqlite"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS CURRENT_GAME ( USER_ID text," \
                                                        " GALLOWS_WORD text," \
                                                        " GALLOWS_STATUS_WORD text," \
                                                        " DESCRIPTION text," \
                                                        " CHARS text, MISTAKES integer)"
        stmt_users = "CREATE TABLE IF NOT EXISTS ALL_USERS ( USER_ID text," \
                     " WINS integer, LOSSES integer,IMAGES_FLG integer )"
        self.conn.execute(stmt)
        self.conn.execute(stmt_users)
        self.conn.commit()

    def add_row_current_game(self, arcg_user_id, arcg_gallows_word,
                             arcg_gallows_status_word, arcg_description, arcg_chars, arcg_mistakes):
        stmt = "INSERT INTO CURRENT_GAME (USER_ID, GALLOWS_WORD," \
               "GALLOWS_STATUS_WORD,DESCRIPTION,CHARS, MISTAKES) VALUES (?, ?, ?, ?, ?, ?)"
        args = (arcg_user_id, arcg_gallows_word,
                arcg_gallows_status_word, arcg_description, arcg_chars, arcg_mistakes, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_row_all_users(self, arau_user_id, arau_wins, arau_losses, arau_images_flg):
        stmt = "INSERT INTO ALL_USERS (USER_ID, WINS," \
               "LOSSES, IMAGES_FLG) VALUES (?, ?, ?, ?)"
        args = (arau_user_id, arau_wins, arau_losses, arau_images_flg, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_row(self, dr_table_name, dr_user_id):
        stmt = "DELETE FROM {} WHERE USER_ID = (?)".format(dr_table_name)
        args = (dr_user_id, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def update_field(self, uf_table_name, uf_field_name, uf_field_value, uf_user_id):
        stmt = "UPDATE {} SET {} = (?) WHERE USER_ID = {}".format(uf_table_name, uf_field_name, uf_user_id)
        args = (uf_field_value, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_items(self, gi_table_name, gi_field_name, gi_user_id):
        stmt = "SELECT {} FROM {} WHERE USER_ID = (?)".format(gi_field_name, gi_table_name)
        args = (gi_user_id,)
        try:
            return [x[0] for x in self.conn.execute(stmt, args)][0]
        except IndexError:
            return False

    def new_player(self, np_user_id):
        self.add_row_all_users(np_user_id, 0, 0, 1)

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
        global lines
        while len(gb_gallows_word) < 5:
            index = random.randint(0, len(lines))
            gb_gallows_word = lines[index].split('|')[0].strip().upper()
            gb_description = lines[index].split('|')[5].strip().upper()
        gb_gallows_status_word = '_'*len(gb_gallows_word)
        if not self.get_items('ALL_USERS', 'WINS', gb_user_id):
            self.new_player(gb_user_id)
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
