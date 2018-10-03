import os

for i in os.listdir(os.getcwd()):
    if i.split('.')[-1] != 'txt':
        continue        
    try:
        hw = open(i, 'r')
    except Exception:
        pass
    else:
        text = hw.readlines()
        hw.close()
        name = i.split('.')
        name = '%s.%s.%s.%s'%(name[2], name[1], name[0], name[3])
        new_hw = open(name, 'w')
        for j in text:
            new_hw.write(j)
        new_hw.close()
        os.system('rm ' + i)
        
