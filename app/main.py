import sys                # возможность импортирования файлов из разных директорий
# при перемещении сервера на другое устройство проследить, что все пути корректны
path_to_hwbot_v2 = '/home/cowberry/Documents/hwbot_v2'
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

weekdays = {'Понедельник': 0, 'Вторник': 1, 'Среда': 2, 'Четверг': 3, 'Пятница': 4, 'Суббота': 5}

def get_date(d):
    year = d[6:]
    if d[3] == '0':
        month = d[4]
    else:
        month = d[3:5]
    day = d[:2]
    return datetime.datetime(int(year), int(month), int(day))

def str_date(d):
    return '{:04d}.{:02d}.{:02d}'.format(d.year, d.month, d.day)


def date_range(base, end):
    base = get_date(base)
    end = get_date(end)
    numdays = (end-base).days + 1
    return ['{:02d}.{:02d}.{:04d}'.format(d.day, d.month, d.year) for d in [base + datetime.timedelta(days=x) for x in range(0, numdays)]]

def make_pairs(l):
    if len(l) % 2 == 0:
        return [[l[2*i], l[2*i+1]] for i in range(0, len(l)//2)]
    else:
        return [[l[2*i], l[2*i+1]] for i in range(0, len(l)//2)] + [[l[-1]]]


##timetable -- расписание. Добавить возможность временных изменений.
##change_timetable -- изменить расписание
##tomorrow -- дз на завтра
##day homework -- дз на определённый день в прошлом (архив) или будущем (собирается из того, что есть на данный момент)
##actual -- заданное дз по всем предметам
##duty table -- список дежурных
##subject homework -- меню с:
    ##I, II, III, IV quarter
    ##from date to date (calender)
##info -- важная информация, которая и так будет отсылаться, просто её можно дополнительно себе прислать
##wish -- пожелания к автору бота
##add_hw -- ищет ближайший день с выбранным предметом и добавляет файл с дз-хой
##rm_hw -- на случай ошибки
##kospekt -- конспекты по предметам
##(admin) push konspekt
##teachers -- таблица (предмет -- учитель (ФИО)). Можно запили добавление/удаление в/из таблицы
##закидывание любых файлов в папки с дз
##перевести все обращения к пользователю на русский
##сделать лог


##в будущем можно научиться посылать фотки (hw), что довольно важно.
# vocation mode когда есть одно статическое домашнее задание на протяжении нескольких дней/недель

bot = telebot.TeleBot(config.token)

wish_bot = telebot.TeleBot(config.wish_token)

# bot.send_message(config.admin_id_list[0], 'test')

def log(message):
    logfile = open(path_to_hwbot_v2 + '/data/log.txt', 'a')
    date = time.strftime("%d.%m.%Y  %H:%M:%S", time.localtime(time.time())) + '  '
    id = str(message.chat.id) + '  '
    name = str(message.chat.first_name) + " " + str(message.chat.last_name) + "  " + str(message.chat.username) + "  "
    text = date + id + name + str(message.text) + "\n"
    logfile.write(text)
    logfile.close()

def admin(message):
    return message.chat.id in config.admin_id_list

def send(message, text, return_fun = False):
    if text == '':
        text = 'Ничего не было найдено.'
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
            bot.send_message(config.admin_id_list[0], 'Ошибка: ' + str(e))
            start(message)
    return wrapper

subjects = ['Алгебра', 'Англ.яз.', 'Биология', 'География', 'Геометрия', 'История', 'Литература', 'Мат.ан.', 'Обществознание', 'Программирование', 'Рус.яз.', 'Физ-ра', 'Физика', 'Химия']

chosen_subjects = {}

def get_hw(message, day, sub = False, hwNotFoundMessage = True):
        d = day.split('.')        
        day = '%s.%s.%s'%(d[2], d[1], d[0])
        name = day + '.txt'
        hw = {}
        if not sub:
            list_of_subjects = subjects
        else:
            list_of_subjects = [sub]
        for subject in list_of_subjects:
            try:
                f = open(path_to_hwbot_v2 + '/data/hw/%s/%s'%(ru_to_en(subject), name), 'r')
            except FileNotFoundError:
                pass
            else:
                # hw[subject] = ''.join(f.readlines())
                hw[subject] = f.readlines()
                f.close()
        if hw == {}:
            if not(hwNotFoundMessage):
                return 0
            send(message,'Домашнее задание на %s отсутсвует'%(day))
            return
        res = day + ':\n'
        files = []
        for subject in hw:
            for string in hw[subject]:
                if string.startswith('file '):
                    files.append('/data/hw/%s/%s'%(ru_to_en(subject), string.split()[1]))
                    hw[subject].remove(string)
        for sub in hw:
            homework = hw[sub]
            res+='<b>%s</b>:\n%s\n'%(en_to_ru(sub), ''.join(homework))
        # if (res == day + ':\n') and mul:
        #     return
        send(message, res)
        # send(message, '\n'.join(files))
        for file_path in files:
            try:
                file = open(path_to_hwbot_v2 + file_path, 'rb')
            except FileNotFoundError:
                pass
                bot.send_message(config.admin_id_list[0], 'Не могу открыть файл %s' %(path_to_hwbot_v2 + file_path))
            else:
                if file_path[-3:] == 'jpg':
                    bot.send_photo(message.chat.id, file)
                else:
                    bot.send_document(message.chat.id, file)
                file.close()



def subject_choose(message, func, subjects_list = []):
    if subjects_list == []:
        subjects_list = subjects
    markup = types.ReplyKeyboardMarkup()
    for i in make_pairs(subjects_list):
        markup.row(*i)
    sent = bot.send_message(message.chat.id, 'выберите предмет:', reply_markup = markup)
    bot.register_next_step_handler(sent, func)

# сделать разные списки доступных команд для админов и неадминов.
# на каждую кнопку по функции.
# следующий декоратор будет решать какую из функций выбирать в зависимости от нажатой кнопки
started = {}
@trye
@bot.message_handler(commands = ["start"])
def start(message):
    if started.get(message.chat.id) == 1:
        return
    started[message.chat.id] = 1
    markup = types.ReplyKeyboardMarkup()
    markup.row('расписание', 'список дежурных', '/start')
    markup.row('д/з на завтра', 'д/з на день', 'заданное сейчас д/з')
    markup.row('д/з по предмету', 'инфо', 'оставить пожелание')
    markup.row('конспект', 'список учителей', '.')
    if admin(message):
        markup.row('admin menu')
    sent = bot.send_message(message.chat.id, 'главное меню:', reply_markup=markup)
    bot.register_next_step_handler(sent, first)

@trye
def first(message):
    del(started[message.chat.id])
    text = message.text
    adm = admin(message)
    log(message)
    if text == 'расписание':
        timetable(message)
    elif adm and text == 'admin menu':
        admin_menu(message)
    elif text == 'д/з на завтра':
        if datetime.datetime.today().hour < 10:
            tomorrow = datetime.date.today()
        else:
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        if datetime.date.isoweekday(datetime.date.today()) == 7:
            tomorrow = tomorrow + datetime.timedelta(days=1)
        tomorrow = tomorrow.strftime("%d.%m.%Y")
        get_hw(message, tomorrow)
        start(message)
    elif text == 'д/з на день':
        hw_on_day(message)
    elif text == 'заданное сейчас д/з':
        dates = [(datetime.date.today() + datetime.timedelta(days=i)).strftime("%d.%m.%Y") for i in range(1, 8)]
        actual = ''
        for d in dates:
            get_hw(message, d, hwNotFoundMessage = False)

        start(message)
    elif text == 'д/з по предмету':
        subject_choose(message, subject_menu)
    elif text == 'список дежурных':
        duty = open(path_to_hwbot_v2 + '/data/dutytable.txt', 'r')
        table_1st = duty.readlines()
        table = []
        duty.close()
        weekday = datetime.datetime.today().weekday()
        for i in table_1st:
            if weekday == weekdays[i.split()[0][:-1]]:
                begin = '<b>'
                end = '</b>'
            elif weekday + 1 == weekdays[i.split()[0][:-1]]:
                begin = '<i>'
                end = '</i>'
            else:
                begin = '<code>'
                end = '</code>'
            i = begin + i.split()[0] + ' ' + ' '.join(i.split()[1:]) + end
            table.append(i)
        send(message, '\n'.join(table))
        start(message)
    elif text == 'инфо':
        infof = open(path_to_hwbot_v2 + '/data/info.txt')
        info = ''.join(infof.readlines())
        infof.close()
        if info == '':
            info = 'Важная информация отсутствует.'
        send(message, info)
        start(message)
    elif text == 'оставить пожелание':
        sent = send(message, 'Введите текст и он будет отправлен создателю данного бота.', return_fun = True)
        bot.register_next_step_handler(sent, wish)
    elif text == 'конспект':
        subject_choose(message, send_konspekt, ['История', 'Мат.ан.', 'Алгебра', 'Геометрия', 'Обществознание'])
    elif text == 'список учителей':
        teachersf = open(path_to_hwbot_v2 + '/data/teachers.txt', 'r')
        teachers = teachersf.readlines()
        teachersf.close()
        send(message, ''.join(teachers))
        start(message)
    else:
        start(message)
@trye
def send_konspekt(message):
    subject = ru_to_en(message.text)
    try:
        konspekt = open(path_to_hwbot_v2 + '/data/konspektus/%s.pdf'%(subject), 'rb')
    except FileNotFoundError:
        send(message, 'Не найдено конспекта по предмету "%s"'%(message.text))
    else:
        bot.send_document(message.chat.id, konspekt)
        konspekt.close()
    finally:
        start(message)


@trye
def wish(message):
    author_info = str(message.chat.first_name) + ' ' + str(message.chat.last_name) + ' @' + str(message.chat.username) + '\n' #str in case of None value
    wish_bot.send_message(config.admin_id_list[0], author_info + message.text)
    send(message, 'Пожелание отправлено.')
    start(message)

#на или с?
# Если задано с 1 на 2, то это:
# 02.09.2018.txt ok
# пробегать по папкам указанным в расписании ok

def get_mode():
    modef = open(path_to_hwbot_v2 + '/data/mode.txt')
    mode = modef.read()
    modef.close()
    return mode

@trye
def subject_menu(message):
    chosen_subjects[message.chat.id] = message.text
    markup = types.ReplyKeyboardMarkup()
    markup.row('1', '2')
    markup.row('3', '4')
    markup.row('диапозон дат')
    sent = bot.send_message(message.chat.id, 'выберете диапозон (цифры -- четверти):', reply_markup = markup)
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
    for d in dates:
        get_hw(message, d, sub = ru_to_en(chosen_subjects[message.chat.id]), hwNotFoundMessage = False)
    start(message)

@trye
def choose_dates(message):
    now = datetime.datetime.now() #Current date
    chat_id = message.chat.id
    date = (now.year,now.month)
    current_shown_dates[chat_id] = date #Saving the current date in a dict
    markup= create_calendar(now.year,now.month, subject = ' ')
    bot.send_message(message.chat.id, "Выберите две даты:", reply_markup=markup)
    active_calendars[message.chat.id] = message.date
    start(message)




@trye
def hw_on_day(message):
    now = datetime.datetime.now() #Current date
    chat_id = message.chat.id
    date = (now.year,now.month)
    current_shown_dates[chat_id] = date #Saving the current date in a dict
    markup= create_calendar(now.year,now.month)
    active_calendars[message.chat.id] = message.date
    bot.send_message(message.chat.id, "Выберите дату:", reply_markup=markup)
    start(message)


chosen_dates = {}
active_calendars = {}

@bot.callback_query_handler(func=lambda call: call.data[0:12] == 'subject-day-')
def get_days(call):
    # send(call.message, '%i\n%i'%(active_calendars[call.message.chat.id], call.message.date))
    if active_calendars.get(call.message.chat.id, 0) != call.message.date:
        bot.answer_callback_query(call.id, text="")
        return
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
            nohw = True
            for dates_elem in dates:
                # get_hw(call.message, dates_elem, sub = ru_to_en(chosen_subjects[chat_id]), hwNotFoundMessage = False)
                if get_hw(call.message, dates_elem, sub = ru_to_en(chosen_subjects[chat_id]), hwNotFoundMessage = False) != 0:
                    nohw = False
            if nohw == True:
                send(call.message, 'Не найдено дз на этот диапозон дат.')
            del(chosen_dates[chat_id])
        bot.answer_callback_query(call.id, text="")

    else:
        #Do something to inform of the error
        pass


#Forked from https://github.com/unmonoqueteclea/calendar-telegram
current_shown_dates={}
@bot.callback_query_handler(func=lambda call: call.data[0:13] == 'calender-day-')
def get_day(call):
    if active_calendars.get(call.message.chat.id, 0) == 0:
        pass
    elif active_calendars.get(call.message.chat.id, 0) != call.message.date:
        bot.answer_callback_query(call.id, text="")
        return
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    if(saved_date is not None):
        day=call.data[13:]
        try:
            date = str(datetime.datetime(int(saved_date[0]),int(saved_date[1]),int(day),0,0,0))
        except Exception as e:
            pass
        else:
            date = '%s.%s.%s'%(date[8:10], date[5:7], date[:4])
            get_hw(call.message, date)
        finally:
            bot.answer_callback_query(call.id, text="")
    else:
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'sub-next-month')
def sub_next_month(call):
    next_month(call, sub = ' ')


@bot.callback_query_handler(func=lambda call: call.data == 'next-month')
def next_month(call, sub = None):
    if active_calendars.get(call.message.chat.id, 0) == 0:
        pass
    elif active_calendars.get(call.message.chat.id, 0) != call.message.date:
        bot.answer_callback_query(call.id, text="")
        return
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
        bot.edit_message_text("Выберите дату:", call.from_user.id, call.message.message_id, reply_markup=markup)
        active_calendars[call.message.chat.id] = call.message.date
        bot.answer_callback_query(call.id, text="")
    else:
        #Do something to inform of the error
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'sub-previous-month')
def sub_previous_month(call):
    previous_month(call, sub = ' ')


@bot.callback_query_handler(func=lambda call: call.data == 'previous-month')
def previous_month(call, sub = None):
    if active_calendars.get(call.message.chat.id, 0) == 0:
        pass
    elif active_calendars[call.message.chat.id] != call.message.date:
        bot.answer_callback_query(call.id, text="")
        return
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
        bot.edit_message_text("Выберите дату:", call.from_user.id, call.message.message_id, reply_markup=markup)
        active_calendars[call.message.chat.id] = call.message.date
        bot.answer_callback_query(call.id, text="")
    else:
        #Do something to inform of the error
        pass

@bot.callback_query_handler(func=lambda call: call.data == 'main-menu')
def main_menu(call):
    bot.answer_callback_query(call.id, text="")
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data[0:13] == 'ignore')
def ignore(call):
    bot.answer_callback_query(call.id, text="")
    pass
#Forked from https://github.com/unmonoqueteclea/calendar-telegram
@trye
def admin_menu(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('test', 'kill', '/start')
    markup.row('change_timetable', 'mode', 'change_info')
    markup.row('add_hw', 'rm_hw', 'push_konspekt')
    markup.row('change_any_hw', 'push_file', 'log')
    sent = bot.send_message(message.chat.id, "admin menu test", reply_markup = markup)
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
        sent = bot.send_message(message.chat.id, 'choose mode:', reply_markup = markup)
        bot.register_next_step_handler(sent, change_mode)
    elif text == 'change_info':
        sent = send(message, 'Введите новую информацию:', return_fun = True)
        bot.register_next_step_handler(sent, change_info)
    elif text == 'add_hw':
        subject_choose(message, add_hw_step)
    elif text == 'rm_hw':
        sent = send(message, 'Введите дату в формате dd.mm.yyyy:', return_fun = True)
        bot.register_next_step_handler(sent, rm_hw_sub_choose)
    elif text == 'push_konspekt':
        subject_choose(message, push_konspekt_subject_choose)
    elif text == 'change_any_hw':
        markup = types.ReplyKeyboardMarkup()
        markup.row('add', 'rm')
        sent = bot.send_message(message.chat.id, 'доавить или удалить?', reply_markup = markup)
        bot.register_next_step_handler(sent, change_any_hw)
    elif text == 'push_file':
        subject_choose(message, push_file_subject_choose)
    elif text == 'log':
        try:
            log_file = open(path_to_hwbot_v2 + '/data/log.txt', 'r')
        except FileNotFoundError:
            send(message, 'бот не смог найти лог')
        else:
            bot.send_document(message.chat.id, log_file)
            log_file.close()
        finally:
            start(message)
    else:
        start(message)

add_or_remove = {}
file_name = {}

@trye
def push_file_subject_choose(message):
    chosen_subjects[message.chat.id] = ru_to_en(message.text)
    sent = send(message, 'Наберите имя файла:', return_fun = True)
    bot.register_next_step_handler(sent, push_file_choose_name)

@trye
def push_file_choose_name(message):
    file_name[message.chat.id] = message.text
    sent = send(message, 'Отошлите файл по предмету "%s":'%(chosen_subjects[message.chat.id]), return_fun = True)
    bot.register_next_step_handler(sent, push_file)

@trye
def push_file(message):
    subject = chosen_subjects[message.chat.id]
    file_id = message.document.file_id
    downloaded_file = bot.download_file(bot.get_file(file_id).file_path)
    file = open(path_to_hwbot_v2 + '/data/hw/%s/%s'%(subject, file_name[message.chat.id] + '.' + message.document.file_name.split('.')[-1]), 'wb')
    file.write(downloaded_file)
    file.close()
    start(message)

@trye
def change_any_hw(message):
    if message.text == 'add':
        add_or_remove[message.chat.id] = 'add'
    elif message.text == 'rm':
        add_or_remove[message.chat.id] = 'rm'
    else:
        start(message)
        return
    subject_choose(message, sub_to_change)

@trye
def sub_to_change(message):
    chosen_subjects[message.chat.id] = ru_to_en(message.text)
    sent = send(message, 'Введите дату в формате dd.mm.yyyy:', return_fun = True)
    bot.register_next_step_handler(sent, date_to_change)

chosen_dates = {}

@trye
def date_to_change(message):
    id = message.chat.id
    d = message.text.split('.')
    message.text = '%s.%s.%s'%(d[2], d[1], d[0]) 
    if add_or_remove[id] == 'add':
        chosen_dates[message.chat.id] = message.text
        sent = send(message, 'Введите домашнее задание по предмету %s на %s:'%(chosen_subjects[id], message.text), return_fun = True)
        bot.register_next_step_handler(sent, add_hw_any)
    elif add_or_remove[id] == 'rm':
        path = path_to_hwbot_v2 + '/data/hw/%s/%s.txt'%(chosen_subjects[id], message.text)
        try:
            os.remove(path)
        except FileNotFoundError:
            send(message, 'нет такого дз')
        finally:
            start(message)

@trye
def add_hw_any(message):
    path = path_to_hwbot_v2 + '/data/hw/%s/%s.txt'%(chosen_subjects[message.chat.id], chosen_dates[message.chat.id])
    hw = open(path, 'w')
    hw.write(message.text)
    hw.close()
    start(message)



@trye
def push_konspekt_subject_choose(message):
    chosen_subjects[message.chat.id] = ru_to_en(message.text)
    sent = send(message, 'Отошлите файл pdf с конспектом по предмету "%s"'%(message.text), return_fun = True)
    bot.register_next_step_handler(sent, push_konspekt)

@trye
def push_konspekt(message):
    subject = chosen_subjects[message.chat.id]
    file_id = message.document.file_id
    downloaded_file = bot.download_file(bot.get_file(file_id).file_path)
    konspekt = open(path_to_hwbot_v2 + '/data/konspektus/%s.pdf'%(subject), 'wb')
    konspekt.write(downloaded_file)
    konspekt.close()
    start(message)



@trye
def rm_hw_sub_choose(message):
    chosen_dates[message.chat.id] = message.text
    weekday = get_date(message.text).weekday()
    list_of_subs = table.get(weekday)
    print(list_of_subs)
    markup = types.ReplyKeyboardMarkup()
    for i in make_pairs(list_of_subs):
        markup.row(*i)
    sent = bot.send_message(message.chat.id, 'Выберите предмет:', reply_markup = markup)
    bot.register_next_step_handler(sent, rm_hw)

@trye
def rm_hw(message):
    path = path_to_hwbot_v2 + '/data/hw/%s/%s.txt'%(ru_to_en(message.text), chosen_dates[message.chat.id])
    try:
        os.remove(path)
    except FileNotFoundError:
        send(message, 'Не найдено файла ' + path)
    else:
        send(message, 'Файл ' + path + ' удалён.')
    finally:
        start(message)

# @trye
# def add_hw(message):
#     subject_choose(messageadd_hw_step)

@trye
def add_hw_step(message):
    chosen_subjects[message.chat.id] = message.text
    sent = send(message, 'Введите дз по предмету "%s"'%(message.text), return_fun = True)
    bot.register_next_step_handler(sent, add_hw_step2)

@trye
def add_hw_step2(message):
    found = False
    for day in range(1, 8):
        if ((datetime.datetime.today() + datetime.timedelta(days = day)).weekday() != 6) and (chosen_subjects.get(message.chat.id) in table.get_all()[(datetime.datetime.today() + datetime.timedelta(days = day)).weekday()]):
            found = True
            break
    if not(found):
        send(message, 'не найдено дня с этим предметом')
        start(message)
        return 0
    day = str_date(datetime.datetime.today() + datetime.timedelta(days = day))
    print(day)
    hwf = open(path_to_hwbot_v2 + '/data/hw/%s/%s.txt'%(ru_to_en(chosen_subjects.get(message.chat.id)), day), 'w')
    hwf.write(message.text)
    hwf.close()
    start(message)

@trye
def change_info(message):
    infof = open(path_to_hwbot_v2 + '/data/info.txt', 'w')
    infof.write(message.text)
    infof.close()
    start(message)

@trye
def change_mode(message):
    text = message.text
    mode = open(path_to_hwbot_v2 + '/data/mode.txt', 'w')
    mode.write(text)
    mode.close()
    bot.send_message(config.admin_id_list[0], 'mode сменён на ' + text)
    start(message)

@trye
def change_timetable(message):
    sent = send(message, 'Введите день и номер пары (weekday(0-5) pair)', return_fun = True)
    bot.register_next_step_handler(sent, choose_new_sub)

@trye
def choose_new_sub(message):
    global command
    text = message.text.split()
    command = [int(text[0]), int(text[1]) - 1]
    subject_choose(message, changing_timetable_confirm)


@trye
def changing_timetable_confirm(message):
    global command
    markup = types.ReplyKeyboardMarkup()
    markup.row('Yes', 'No')
    new = message.text
    command.append(new)
    sent = bot.send_message(message.chat.id, 'Вы уверены, что хотите внести изменения?', reply_markup = markup)
    bot.register_next_step_handler(sent, changing_timetable_final)


@trye
def changing_timetable_final(message):
    global command
    text = message.text
    send(message, text)
    if text == 'Yes':
        weekday, n, new = command
        if weekday not in range(6):
            send(message, 'инкорректный день недели')
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
            time.sleep(1)
