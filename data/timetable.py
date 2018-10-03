# когда-нибудь можно добавить поддержку английского. Просто для фана.
# Хотя у меня и так почти всё на английском
path_to_hwbot_v2 = '/home/cowberry/Documents/hwbot_v2'

def get(day_of_week):
    table = open(path_to_hwbot_v2 + '/data/timetable.txt', 'r')
    ret = table.readlines()[day_of_week][:-1].split(';')
    table.close()
    return ret

def get_all():
    ret = []
    for i in range(6):
        ret.append(get(i))
    return ret

def change(day_of_week, index, new_name):
    table = open(path_to_hwbot_v2 + '/data/timetable.txt', 'r')
    text = table.readlines()
    table.close()
    temp = []
    for i in text:
        temp.append(i.split(';'))
    text = temp
    if index < len(text[day_of_week]):
        text[day_of_week][index] = new_name
    else:
        text[day_of_week].append(new_name)
    temp = []
    for i in text:
        if i == ['\n']:
            temp.append(';')
            continue
        temp.append(';'.join(i))
    text = temp
    table = open(path_to_hwbot_v2 + '/data/timetable.txt', 'w')
    for i in text:
        table.write(i)
    table.close()
