#Forked from https://github.com/unmonoqueteclea/calendar-telegram
from telebot import types
import calendar

def create_calendar(year,month, subject = None):
    markup = types.InlineKeyboardMarkup()
    #First row - Month and Year
    row=[]
    row.append(types.InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data="ignore"))
    markup.row(*row)
    #Second row - Week Days
    week_days=["M","T","W","R","F","S","U"]
    row=[]
    for day in week_days:
        row.append(types.InlineKeyboardButton(day,callback_data="ignore"))
    markup.row(*row)

    my_calendar = calendar.monthcalendar(year, month)
    if subject:
        callback_name = 'subject-day-'
    else:
        callback_name = 'calender-day-'
    for week in my_calendar:
        row=[]
        for day in week:
            if(day==0):
                row.append(types.InlineKeyboardButton(" ",callback_data="ignore"))
            else:
                row.append(types.InlineKeyboardButton(str(day),callback_data= callback_name+str(day)))
        markup.row(*row)
    #Last row - Buttons
    row=[]
    if subject:
        adding = 'sub-'
    else:
        adding = ''
    row.append(types.InlineKeyboardButton("<",callback_data=adding + "previous-month"))
    row.append(types.InlineKeyboardButton("main menu",callback_data="main-menu"))
    row.append(types.InlineKeyboardButton(">",callback_data=adding + "next-month"))
    markup.row(*row)
    return markup

markup = create_calendar(2018, 8)
print(markup.keyboard)
