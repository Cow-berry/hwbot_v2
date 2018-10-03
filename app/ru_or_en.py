en_ru = {'Algebra': 'Алгебра',
         'Biology': 'Биология',
         'Chemistry': 'Химия',
         'English': 'Англ.яз.',
         'Geography': 'География',
         'Geometry': 'Геометрия',
         'History': 'История',
         'Literature': 'Литература',
         'Math.an.': 'Мат.ан.',
         'PE': 'Физ-ра',
         'Physics': 'Физика',
         'Programming': 'Программирование',
         'Russian': 'Рус.яз.',
         'Social Studies': 'Обществознание'}

# print(en_ru)
keys = list(en_ru.keys())
print(sorted(keys))
ru_en = {}
for i in range(len(keys)):
    ru_en[en_ru[keys[i]]]=keys[i]
#ru_en -- ru => en
#en_ru -- en => ru

def en_to_ru(name):
    return en_ru.get(name, name)

def ru_to_en(name):
    return ru_en.get(name, name)

print(sorted(list(ru_en.keys())))
