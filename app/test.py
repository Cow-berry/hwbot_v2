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
print(get_hw('13.08.2018'))
