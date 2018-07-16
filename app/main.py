import sys                # возможность импортирования файлов из разных директорий
sys.path.append('/home/cowberry/Documents/hwbot_v2') # для доступа к расписанию
import data.timetable          # расписание
import time               # время и дата
import config             # токен и id-шники админов
import telebot            # удобная работа с Telegram API
from pathlib import Path  # для проверки существования файла
from telebot import types # для крутых клавиатур
import os                 # исполнение консольных команд
from importlib import reload  # позволяет переимпортировать модуль, если он был изменён в процессе (timetable.py)


# tommorow -- дз на завтра
# actual -- заданное дз по всем предметам
# timetable -- расписание. Добавить возможность временных изменений.
# duty table -- список дежурных
# subject homework -- дз по предмету
# day homework -- дз на определённый день в прошлом (архив) или будущем (собирается из того, что есть на данный момент)
# info -- важная информация, которая и так будет отсылаться, просто её можно дополнительно себе прислать
# wish -- пожелания к автору бота
# kospekt -- конспекты по предметам

bot = telebot.TeleBot(config.token)

# bot.send_message(config.admin_id_list[0], 'test')

def log(message):
    logfile = open("data/log.txt", 'a')
    date = time.strftime("%d.%m.%Y  %H:%M:%S", time.localtime(time.time())) + '  '
    id = str(message.chat.id) + '  '
    name = message.chat.first_name + " " + message.chat.last_name + "  " + str(message.chat.username) + "  "
    text = date + id  + name + message.text + "\n"
    logfile.write(text)
    logfile.close()

def admin(message):
    return message.chat.id in config.admin_id_list

def send(message, text, return_fun = False):
    s = bot.send_message(message.chat.id, text, parse_mode = 'HTML')
    if not(return_fun):
        s
    else:
        return s
#############################################################################################################
# полная остановка бота
def kill(message):
    if admin(message):
        bot.send_message(message.chat.id, 'полная остановка бота!')
        os.system('killall python3')
    start(message)


def test(message):
    log(message)
    bot.send_message(message.chat.id, 'test')
    start(message)

# сделать разные списки доступных команд для админов и неадминов.
# на каждую кнопку по функции.
# следующий декаратор будет решать какую из функций выбирать в зависимости от нажатой кнопки
@bot.message_handler(commands = ["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('timetable')
    send(message, 'hello' + str(admin(message)))
    if admin(message):
        markup.row('admin menu')
    sent = bot.send_message(message.chat.id, "keyboard test", reply_markup=markup)
    bot.register_next_step_handler(sent, first)

def first(message):
    text = message.text
    adm = admin(message)
    if text == 'timetable':
        timetable(message)
    elif adm and text == 'admin menu':
        admin_menu(message)
    else:
        start(message)

def admin_menu(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('test', 'kill')
    markup.row('change_timetable')
    sent = bot.send_message(message.chat.id, "admin menu test", reply_markup=markup)
    bot.register_next_step_handler(sent, admin_reply)

def admin_reply(message):
    text = message.text
    if text == 'test':
        test(message)
    elif text == 'kill':
        kill(message)
    elif text == 'change_timetable':
        change_timetable(message)
    else:
        start(message)

def change_timetable(message):
    sent = send(message, 'Введите изменения:', return_fun = True)
    bot.register_next_step_handler(sent, changing_timetable_which)

def changing_timetable_which(message):
    text = message.text.split()
    dow = text[0]
    n = int(text[1])-1
    new = text[2]
    mess = "%s[%i] = '%s\n'"%(dow, n, new)
    sent = send(message, mess, return_fun = True)
    bot.register_next_step_handler(sent, changing_timetable_confirm(mess))
    start(message)

def changing_timetable_confirm(message, mess):
    markup = types.ReplyKeyboardMarkup()
    markup.row('Yes', 'No')
    sent = bot.send_message(message.chat.id, 'Вы уверены, что хотите внести изменения?')
    bot.register_next_step_handler(sent, changing_timetable_final(mess))

def changing_timetable_final(message, mess):
    text = message.text
    if text == 'Yes':
        file = open('data/timetable.py', 'a')
        file.write(mess)
        file.close()
    start(message)




def timetable(message):
    reload(data.timetable)
    text = ''
    days_of_week = [data.timetable.monday, data.timetable.tuesday, data.timetable.wednesday, data.timetable.thursday, data.timetable.friday, data.timetable.saturday]
    days_of_week_rus = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
    isoweek = time.localtime(time.time())[6]
    for i in range(6):
        if (i == isoweek) or ((i == 0) and (isoweek == 6)):
            space = '        '
            begin = '<b>'
            end = '</b>'
            # text_to_add = '<b>' + text_to_add + '</b>'
        elif (i == isoweek - 1):
            space = '    '
            begin = '<i>'
            end = '</i>'
        else:
            space = '    '
            begin = '<code>'
            end = '</code>'

        text_to_add = begin + days_of_week_rus[i] + ':\n' + space + ('\n'+space).join(days_of_week[i]) + '\n' + end
        text += text_to_add
    send(message, text)
    start(message)


if __name__ == '__main__':
    # bot.send_message(config.admin_id_list[0], "<code> def cool_fun(a, b, c):\n print(a', 1, c)</code>", parse_mode = 'HTML')
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)

# можно создать errorbot, который будет посылать сообщения об ошибке

#
#     @bot.message_handler(commands = ['a'])
#     def add(message):
#         file = open('data/timetable.py', 'a')
#         file.write('monday.append(3)\n')
#         file.close()
