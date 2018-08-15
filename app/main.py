import sys                # возможность импортирования файлов из разных директорий
# при перемещении сервера на другое устройство проследить, что все пути корректны
path_to_hwbot_v2 = '/home/tolik/Documents/hwbot_v2'
sys.path.append(path_to_hwbot_v2) # для доступа к расписанию
import data.timetable as table       # расписание
import datetime, time               # время и дата
import config             # токен и id-шники админов
import telebot            # удобная работа с Telegram API
from pathlib import Path  # для проверки существования файла
from telebot import types # для крутых клавиатур
import os                 # исполнение консольных командcommand = [] # commadn to execute/paste. Переменная создана, т.к. между функциями не сделать передачи.
from telegramcalendar import create_calendar
from ru_or_en import ru_to_en, en_to_ru

quarters_dates = {1: {'begin': '01.09.2018', 'end': '27.10.2018'}, 2: {'begin': '8.11.2018', 'end': '27.12.2018'}, 3: {'begin': '11.01.2019', 'end': '23.03.2019'}, 4: {'begin': '02.04.2019', 'end': '25.05.2018'}}

def get_date(d):
    year = d[6:]
    if d[3] == '0':
        month = d[4]
    else:
        month = d[3:5]
    day = d[:2]
    return datetime.datetime(int(year), int(month), int(day))

def str_date(d):
    return '{:02d}.{:02d}.{:04d}'.format(d.day, d.month, d.year)


def date_range(base, end):
    base = get_date(base)
    end = get_date(end)
    numdays = (end-base).days + 1
    return [str_date(d) for d in [base + datetime.timedelta(days=x) for x in range(0, numdays)]]

def make_pairs(l):
    if len(l) % 2 == 0:
        return [[subjects[2*i], subjects[2*i+1]] for i in range(0, len(subjects)//2)]
    else:
        return [[subjects[2*i], subjects[2*i+1]] for i in range(0, len(subjects)//2)] + [[l[-1]]]


##timetable -- расписание. Добавить возможность временных изменений.
##change_timetable -- изменить расписание
##tomorrow -- дз на завтра
##day homework -- дз на определённый день в прошлом (архив) или будущем (собирается из того, что есть на данный момент)
##actual -- заданное дз по всем предметам
##duty table -- список дежурных
# subject homework -- меню с:
    # I, II, III, IV quarter
    # from date to date (calender)
# info -- важная информация, которая и так будет отсылаться, просто её можно дополнительно себе прислать
# wish -- пожелания к автору бота
# kospekt -- конспекты по предметам
# teachers -- таблица (предмет -- учитель (ФИО)). Можно запили добавление/удаление в/из таблицы

# в будущем можно научиться посылать фотки (hw), что довольно важно.
# vocation mode когда есть одно статическое домашнее задание на протяжении нескольких дней/недель

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
    if text == '':
        text = 'Nothing was found'
    s = bot.send_message(message.chat.id, text , parse_mode = 'HTML')
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

#декаратор для избежания вечно повторяющихся ошибок
def trye(func):
    def wrapper(message):
        try:
            func(message)
        except Exception as e:
            bot.send_message(310802215, 'Ошибка: ' + str(e))
            start(message)
    return wrapper

subjects = ['Алгебра', 'Англ.яз.', 'Биология', 'География', 'Геометрия', 'История', 'Литература', 'Мат.ан.', 'Обществознание', 'Программирование', 'Рус.яз.', 'Физ-ра', 'Физика', 'Химия']

chosen_subjects = {}

def get_hw(day, sub = None):
        name = day + '.txt'
        hw = {}
        if not sub:
            list_of_subjects = subjects
        else:
            list_of_subjects = [sub]
        for subject in list_of_subjects:
            try:
                f = open(path_to_hwbot_v2 + '/data/hw/%s/%s'%(subject, name), 'r')
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

@bot.message_handler(commands = ["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('timetable', 'duty')
    markup.row('tomorrow', 'hw on day')
    markup.row('actual', 'subject')
    markup.row('/start')
    if admin(message):
        markup.row('admin menu')
    sent = bot.send_message(message.chat.id, 'main menu:', reply_markup=markup)
    bot.register_next_step_handler(sent, first)

@trye
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
        for d in dates:
            hw = get_hw(d)
            if hw == 'Домашнее задание на %s отсутсвует'%(d):
                continue
            actual += d + ':\n' + hw
        if not(actual):
            send(message, 'Не найдено ни одного домашнего задания на ближайшую неделю')
        else:
            send(message, actual)
        start(message)
    elif text == 'subject':
        markup = types.ReplyKeyboardMarkup()
        for i in make_pairs(subjects):
            markup.row(*i)
        sent = bot.send_message(message.chat.id, 'choose subject:', reply_markup = markup)
        bot.register_next_step_handler(sent, subject_menu)
    elif text == 'duty':
        duty = open(path_to_hwbot_v2 + '/data/dutytable.txt', 'r')
        table = duty.readlines()
        duty.close()
        send(message, '\n'.join(table))
        start(message)
    else:
        start(message)

#на или с?
# Если задано с 1 на 2, то это:
# 02.09.2018.txt ok
# пробегать по папкам указанным в расписании ok

def get_mode():
    modef = open(path_to_hwbot_v2 + '/app/mode.txt')
    mode = modef.read()
    modef.close()
    return mode

@trye
def subject_menu(message):
    chosen_subjects[message.chat.id] = message.text
    markup = types.ReplyKeyboardMarkup()
    markup.row('1', '2')
    markup.row('3', '4')
    markup.row('date to date')
    sent = bot.send_message(message.chat.id, 'choose date range:', reply_markup = markup)
    bot.register_next_step_handler(sent, give_subject_hw)

@trye
def give_subject_hw(message):
    text = message.text
    mode = get_mode()
    try:
        text = int(text)
    except ValueError:
        choose_dates(message)#calender work
        return 0
    else:
        try:
            mode = int(mode)
        except ValueError:
            pass
        else:
            sub = text - mode
            if sub>0:
                send(message, 'Нет дз на следующие четверти')
                start(message)
                return 0
    dates = date_range(quarters_dates[text]['begin'], quarters_dates[text]['end'])
    hw = [d + ':\n' + get_hw(d, sub = ru_to_en(chosen_subjects[message.chat.id])) for d in dates if not(get_hw(d, sub = ru_to_en(chosen_subjects[message.chat.id])) == 'Домашнее задание на %s отсутсвует'%(d))]
    send(message, '\n'.join(hw))
    start(message)

@trye
def choose_dates(message):
    now = datetime.datetime.now() #Current date
    chat_id = message.chat.id
    date = (now.year,now.month)
    current_shown_dates[chat_id] = date #Saving the current date in a dict
    markup= create_calendar(now.year,now.month, subject = ' ')
    bot.send_message(message.chat.id, "Please, choose dates", reply_markup=markup)




@trye
def hw_on_day(message):
    now = datetime.datetime.now() #Current date
    chat_id = message.chat.id
    date = (now.year,now.month)
    current_shown_dates[chat_id] = date #Saving the current date in a dict
    markup= create_calendar(now.year,now.month)
    bot.send_message(message.chat.id, "Please, choose a date test", reply_markup=markup)


chosen_dates = {}

@bot.callback_query_handler(func=lambda call: call.data[0:12] == 'subject-day-')
def get_day(call):
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    if(saved_date is not None):
        day=call.data[12:]
        d = str(datetime.datetime(int(saved_date[0]),int(saved_date[1]),int(day),0,0,0))
        d = '%s.%s.%s'%(d[8:10], d[5:7], d[:4])
        send(call.message, d)
        if chosen_dates.get(chat_id, []) == []:
            chosen_dates[chat_id] = [d]
        else:
            chosen_dates[chat_id].append(d)
            begin = get_date(chosen_dates[chat_id][0])
            end = get_date(d)
            if (begin-end).days > 0:
                begin, end = end, begin
            subject = chosen_subjects[chat_id]
            dates = date_range(str_date(begin), str_date(end))
            hw = [dates_elem + ':\n' + get_hw(dates_elem, sub = ru_to_en(chosen_subjects[chat_id])) for dates_elem in dates if not(get_hw(dates_elem, sub = ru_to_en(chosen_subjects[chat_id])) == 'Домашнее задание на %s отсутсвует'%(dates_elem))]
            send(call.message, '\n'.join(hw))
            del(chosen_dates[chat_id])
            start(call.message)
        bot.answer_callback_query(call.id, text="")

    else:
        #Do something to inform of the error
        pass


#Forked from https://github.com/unmonoqueteclea/calendar-telegram
current_shown_dates={}
@bot.callback_query_handler(func=lambda call: call.data[0:13] == 'calender-day-')
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
        pass
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'sub-next-month')
def sub_next_month(call):
    next_month(call, sub = ' ')


@bot.callback_query_handler(func=lambda call: call.data == 'next-month')
def next_month(call, sub = None):
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
        markup= create_calendar(year,month, subject = sub)
        bot.edit_message_text("Please, choose a date", call.from_user.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, text="")
    else:
        #Do something to inform of the error
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'sub-previous-month')
def sub_previous_month(call):
    previous_month(call, sub = ' ')


@bot.callback_query_handler(func=lambda call: call.data == 'previous-month')
def previous_month(call, sub = None):
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
        markup= create_calendar(year,month, subject = sub)
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
@trye
def admin_menu(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('test', 'kill')
    markup.row('change_timetable', 'mode')
    markup.row('/start')
    sent = bot.send_message(message.chat.id, "admin menu test", reply_markup=markup)
    bot.register_next_step_handler(sent, admin_reply)

@trye
def admin_reply(message):
    text = message.text
    if text == 'test':
        test(message)
    elif text == 'kill':
        kill(message)
    elif text == 'change_timetable':
        change_timetable(message)
    elif text == 'mode':
        markup = types.ReplyKeyboardMarkup()
        markup.row('1', '2')
        markup.row('3', '4')
        markup.row('vocation')
        sent = bot.send_message(message.chat.id, 'choose mode:')
        bot.register_next_step_handler(sent, change_mode)
    else:
        start(message)

@trye
def change_mode(message):
    text = message.text
    mode = open(path_to_hwbot_v2 + '/app/mode.txt', 'w')
    mode.write(text)
    mode.close()
    send(config.admin_id_list[0], 'mode changed to ' + text)
    start(message)

@trye
def change_timetable(message):
    sent = send(message, 'Введите изменения:', return_fun = True)
    bot.register_next_step_handler(sent, changing_timetable_confirm)

@trye
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

@trye
def changing_timetable_final(message):
    global command
    text = message.text
    send(message, text)
    if text == 'Yes':
        table.change(*command)
        send(message, 'записано')
    start(message)



@trye
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
        elif (i == isoweek + 1):
            space = '        '
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
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
