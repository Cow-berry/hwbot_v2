import sys                # возможность импортирования файлов из разных директорий
sys.path.append('/home/tolik/Documents/hwbot_v2') # для доступа к расписанию
import data.timetable as table       # расписание
import datetime, time               # время и дата
import config             # токен и id-шники админов
import telebot            # удобная работа с Telegram API
from pathlib import Path  # для проверки существования файла
from telebot import types # для крутых клавиатур
import os                 # исполнение консольных командcommand = [] # commadn to execute/paste. Переменная создана, т.к. между функциями не сделать передачи.
from telegramcalendar import create_calendar

##timetable -- расписание. Добавить возможность временных изменений.
##change_timetable -- изменить расписание
##tomorrow -- дз на завтра
##day homework -- дз на определённый день в прошлом (архив) или будущем (собирается из того, что есть на данный момент)
# actual -- заданное дз по всем предметам
# duty table -- список дежурных
# subject homework -- дз по предмету
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

subjects = ['Algebra', 'Biology', 'Chemistry', 'English', 'Geography', 'Geometry', 'History', 'Literature', 'Math.an.', 'PE', 'Physics', 'Programming', 'Russian', 'Social Studies']

def get_hw(day):
        name = day + '.txt'
        hw = {}
        for subject in subjects:
            try:
                f = open('/home/tolik/Documents/hwbot_v2/data/hw/%s/%s'%(subject, name), 'r')
            except FileNotFoundError:
                pass
            else:
                hw[subject] = ''.join(f.readlines())
                f.close()
        if hw == {}:
            return 'Домашнее задание на %s отсутсвует'%(day)
        res = ''
        for i in hw:
            sub = i
            homework = hw[i]
            res+='<b>%s</b>:\n%s'%(sub, homework)
        return res




# сделать разные списки доступных команд для админов и неадминов.
# на каждую кнопку по функции.
# следующий декоратор будет решать какую из функций выбирать в зависимости от нажатой кнопки

# в будущем можно научиться посылать фотки, что довольно важно.
# vocation mode когда есть одно статическое домашнее задание на протяжении нескольких дней/недель
@bot.message_handler(commands = ["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('timetable', 'duty')
    markup.row('tomorrow', 'hw on day')
    markup.row('actual')
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
    elif text == 'tomorrow':
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        if datetime.date.isoweekday(datetime.date.today()) == 6 :
            tomorrow = tomorrow + datetime.timedelta(days=1)
        tomorrow = tomorrow.strftime("%d.%m.%Y")
        send(message, get_hw(tomorrow))
        start(message)
    elif text == 'hw on day':
        hw_on_day(message)
    elif text == 'actual':
        dates = [(datetime.date.today() + datetime.timedelta(days=i)).strftime("%d.%m.%Y") for i in range(1, 8)]
        actual = ''
        for date in dates:
            hw = get_hw(date)
            if hw == 'Домашнее задание на %s отсутсвует'%(date):
                continue
            actual += date + ':\n' + hw
        if not(actual):
            send(message, 'Не найдено ни одного домашнего задания на ближайшую неделю')
        else:
            send(message, actual)
        start(message)
    else:
        start(message)

#на или с?
# Если задано с 1 на 2, то это:
# 02.09.2018.txt ok
# пробегать по папкам указанным в расписании ok

def hw_on_day(message):
    now = datetime.datetime.now() #Current date
    chat_id = message.chat.id
    date = (now.year,now.month)
    current_shown_dates[chat_id] = date #Saving the current date in a dict
    markup= create_calendar(now.year,now.month)
    bot.send_message(message.chat.id, "Please, choose a date", reply_markup=markup)

#Forked from https://github.com/unmonoqueteclea/calendar-telegram
current_shown_dates={}
@bot.callback_query_handler(func=lambda call: call.data[0:13] == 'calendar-day-')
def get_day(call):
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    if(saved_date is not None):
        day=call.data[13:]
        date = str(datetime.datetime(int(saved_date[0]),int(saved_date[1]),int(day),0,0,0))
        date = '%s.%s.%s'%(date[8:10], date[5:7], date[:4])
        bot.send_message(chat_id, get_hw(date), parse_mode = 'HTML')
        bot.answer_callback_query(call.id, text="")

    else:
        #Do something to inform of the error
        pass
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'next-month')
def next_month(call):
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    if(saved_date is not None):
        year,month = saved_date
        month+=1
        if month>12:
            month=1
            year+=1
        date = (year,month)
        current_shown_dates[chat_id] = date
        markup= create_calendar(year,month)
        bot.edit_message_text("Please, choose a date", call.from_user.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, text="")
    else:
        #Do something to inform of the error
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'previous-month')
def previous_month(call):
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    if(saved_date is not None):
        year,month = saved_date
        month-=1
        if month<1:
            month=12
            year-=1
        date = (year,month)
        current_shown_dates[chat_id] = date
        markup= create_calendar(year,month)
        bot.edit_message_text("Please, choose a date", call.from_user.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, text="")
    else:
        #Do something to inform of the error
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'main-menu')
def main_menu(call):
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data[0:13] == 'ignore')
def ignore(call):
    pass
#Forked from https://github.com/unmonoqueteclea/calendar-telegram
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
    bot.register_next_step_handler(sent, changing_timetable_confirm)

def changing_timetable_confirm(message):
    global command
    markup = types.ReplyKeyboardMarkup()
    markup.row('Yes', 'No')
    text = message.text.split()
    day_of_week = int(text[0])
    n = int(text[1])-1
    new = text[2]
    command = [day_of_week, n, new]
    sent = bot.send_message(message.chat.id, 'Вы уверены, что хотите внести изменения?', reply_markup = markup)
    bot.register_next_step_handler(sent, changing_timetable_final)

def changing_timetable_final(message):
    global command
    text = message.text
    send(message, text)
    if text == 'Yes':
        table.change(*command)
        send(message, 'записано')
    start(message)




def timetable(message):
    text = ''
    days_of_week = table.get_all()
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
