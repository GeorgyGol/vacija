# %load vacija.py
 

import pandas as pd
import re
from datetime import datetime as dt
import numpy as np
import io
import sys


__version__=1.3
#коэффициенты амортизационных отчислений

#k_amo={'panel': (0.7, ('панел',)), 
#       'brick': (0.8, ('кирпич', 'кирич', 'кирпин')), 
#       'monolit': (1, ('монолит',)), 
#       'block':(1, ('блоч', 'газобетон', 'шлак', 'газосили')), 
#       'log':(2.2, ('дерев', 'бревен', 'щитов')), 
#       'clay':(3.3, ('глин',)), 
#       'carcas': (6.6, ('саман','каркасно-засыпной',)), 
#       'mixt':(0.7, ('смешан',)), 
#       'other':(1, ('иные',)),
#       'bad_series':(0.3, ('К-7', 'K-7', 'К-6', 'K-6', r'1605-AM/5', r'1605-AM/5',
#                                'II-32', 'II-35', '1605-AM', '1605-AM', '1-МГ-300', '1-MГ-300'))}

# коэффициенты срока жизни здания. Срок жизни = 100 * коэфф.
k_amo={'panel': (0.7, ('панел',)), 
       'brick': (1.0, ('кирпич', 'кирич', 'кирпин')), 
       'monolit': (1.5, ('монолит',)), 
       'block':(1, ('блоч', 'газобетон', 'шлак', 'газосили')), 
       'log':(0.22, ('дерев', 'бревен', 'щитов')), 
       'clay':(0.33, ('глин',)), 
       'carcas': (0.66, ('саман','каркасно-засыпной',)), 
       'mixt':(0.7, ('смешан',)), 
       'other':(1, ('иные',)),
       'bad_series':(0.3, ('К-7', 'K-7', 'К-6', 'K-6', r'1605-AM/5', r'1605-AM/5',
                                'II-32', 'II-35', '1605-AM', '1605-AM', '1-МГ-300', '1-MГ-300'))}

null_val={'Не заполнено': np.nan}

k_dila=0.7 #порог ветхости - все, что больше - ветхое

def set_type_kam(d):
    '''set type and k_am for houses'''
    for k, v in k_amo.items():
        for v_i in v[1]:
            msk=d['wall_type'].str.lower().str.contains(v_i) | d['seria'].str.lower().str.contains(v_i)
            d.ix[msk, 'kam']=v[0]
            d.ix[msk, 'type_kam']=k
    return d

def calc_aging_koef(cur_year, dt_frame): #функция расчета износа здания, возвращает серию в процентах
    #return (cur_year - dt_frame['year']) * dt_frame['kam']/100 # вариант с коэф. амортизации - не нравится
    return (cur_year-dt_frame['year'])/(dt_frame['kam']*100) # в этом варианте коэф. определяет продолжительность жизни задния

def calc_percent_wear(d, year=dt.now().year):
    #d['tear']=(year - d['year'])*d['kam']/100
    d['tear']=calc_aging_koef(year, d)
    d.ix[d['wreck'], 'tear']=1
    return d[d['tear'].notnull()]

bar_colors=('lightgray', 'burlywood', 'lightblue', 'maroon', 'plum', 'lightgreen', 'peru')

def clean_for_research1(dtfm):
    dtf=dtfm
    dtf['year']=dtf[['build_year', 'working_year']].replace(null_val).astype(float).max(axis=1)
    dtf['wreck']=dtf['wreck'].apply(lambda x: x.lower() =='да')
    dtf.drop(['build_year', 'working_year'], axis=1, inplace=True)
    #tula specific, moscow specific
    dtf['seria']=dtf['seria'].str.upper()
    dtf.replace({'year':{960:1960, 2975:1975, 2850:1850}, 
                 'seria':{'НЕТ':'НЕ ЗАПОЛНЕНО', 'НЕ УКАЗАН':'НЕ ЗАПОЛНЕНО', 'Б/Н':'НЕ ЗАПОЛНЕНО', 'ПОВТ. ПРИМ.':'НЕ ЗАПОЛНЕНО',
                          'ТИПОВОЙ':'НЕ ЗАПОЛНЕНО', 'НЕ ПРИСВОЕН':'НЕ ЗАПОЛНЕНО', 'ПОВТ.ПРИМ.':'НЕ ЗАПОЛНЕНО',
                          'НЕТ ДАНЕНЫХ':'НЕ ЗАПОЛНЕНО', 'Н/Д':'НЕ ЗАПОЛНЕНО', '----':'НЕ ЗАПОЛНЕНО', 'ПАНЕЛЬНЫЙ (LL-49)':'II-49',
                          'ПОВТ.ПРИМ':'НЕ ЗАПОЛНЕНО', 'ЖИЛОЙ,':'НЕ ЗАПОЛНЕНО', 'ЖИЛОЙ':'НЕ ЗАПОЛНЕНО', 'НЕ ОПРЕДЕЛЕНО':'НЕ ЗАПОЛНЕНО', 
                          'НЕТ ДАННЫХ':'НЕ ЗАПОЛНЕНО', '-':'НЕ ЗАПОЛНЕНО', 'ОТСУТСТВУЕТ':'НЕ ЗАПОЛНЕНО','ПОВТ.ПР.':'НЕ ЗАПОЛНЕНО', 
                          'ПОВТОРНЫЙ ПРОЕКТ':'НЕ ЗАПОЛНЕНО', 'ОТСУТСТВУЮТ ПОДТВЕРЖДАЮЩИЕ ДОКУМЕНТЫ':'НЕ ЗАПОЛНЕНО', 'ЖИЛОЕ':'НЕ ЗАПОЛНЕНО', 
                          'ПОВТОРНОГО ПРИМЕНЕНИЯ':'НЕ ЗАПОЛНЕНО', 'ПОВТОРНО ПРИМИНИМ.':'НЕ ЗАПОЛНЕНО','НЕТ ИНФОРМАЦИИ':'НЕ ЗАПОЛНЕНО',
                          'ИНВИДУАЛЬНЫЙ ПРОЕКТ':'ИНД', 'ЖИЛОЙ.':'НЕ ЗАПОЛНЕНО', 'НЕ УКАЗАННО':'НЕ ЗАПОЛНЕНО','МНДИВИДУАЛЬНЫЙ':'ИНД',
                          'ИНЖИВИДУАЛЬНЫЙ':'ИНД', 'НЕ ИМЕЕТСЯ':'НЕ ЗАПОЛНЕНО', 'ИНАЯ':'НЕ ЗАПОЛНЕНО','ТИПОВЫЙ':'НЕ ЗАПОЛНЕНО',
                          'НЕТИПОВАЯ ЗАСТРОЙКА':'ИНД','НЕ УСТАНОВЛЕН':'НЕ ЗАПОЛНЕНО', 'ПЯТИЭТАЖНЫЙ':'НЕ ЗАПОЛНЕНО', 'ЭКПЕРИМ.':'ИНД',
                          'ЭКСПЕРИМЕНТАЛЬНЫЙ':'ИНД', 'ИНОЙ':'НЕ ЗАПОЛНЕНО','ПОВТОРНОЕ ПРИМЕНЕНИЕ':'НЕ ЗАПОЛНЕНО',
                          '17-ТИ ЭТАЖНЫЙ 3-Х СЕКЦИОННЫЙ ЖИЛОЙ ДОМ НА БАЗЕ БЛОК-СЕКЦИЙ СИСТЕМЫ ГМС-2001 С ПЕРВЫМ ЖИЛЫМ ЭТАЖОМ':'ГМС-2001'}, 
                'living_square':{'Не заполнено': np.nan}, 
                'wall_type':{'Не заполнено': 'Иные'}}, 
                inplace=True)
    
    #dtf['seria']=dtf['seria'].str.replace(r'II', 'П')
    #dtf['seria']=dtf['seria'].str.replace(r'I', '1')
    #dtf['seria']=dtf['seria'].str.replace(r', \(.+\)', '')
    dtf['seria']=dtf['seria'].str.replace(r'!', 'I')
    dtf['seria']=dtf['seria'].str.replace(r'-\s?-', '-')
    dtf['seria']=dtf['seria'].str.replace(r'\*', '')
    dtf['seria']=dtf['seria'].str.replace(r'\s{2,}', ' ')
    dtf['seria']=dtf['seria'].str.replace(r'-?КИ[A-Я]+', 'КИРПИЧНЫЙ')
    dtf['seria']=dtf['seria'].str.replace(r'К[О,П,Э, Л]{3}', 'КОПЭ')
    dtf['seria']=dtf['seria'].str.replace(r'\\', r'/')
    dtf['seria']=dtf['seria'].str.replace(r'-?ПАН[A-Я]+', 'ПАНЕЛЬНЫЙ')
    dtf['seria']=dtf['seria'].str.replace(r'\?', '')
    dtf['seria']=dtf['seria'].str.replace(r'СЕРИЯ', '')
    
    dtf.ix[dtf['seria'].str.contains('инд', case=False), 'seria']='ИНД'
    dtf.ix[dtf['seria'].str.contains('ВУЛ[А,Ы]Х', case=False), 'seria']='БАШНЯ ВУЛЫХА'
    
    dtf.ix[dtf['seria'].str.contains('инив', case=False), 'seria']='ИНД'
    dtf.ix[dtf['seria'].str.contains('идив', case=False), 'seria']='ИНД'
    dtf['seria']=dtf['seria'].str.strip()
       
    try:
        f_lsqr=dtf.ix[dtf['address'].str.contains('ш. Варшавское, д. 144, к. 2'), 'living_square'].values[0]
        dtf.ix[dtf['address'].str.contains('ш. Варшавское, д. 144, к. 1'), 'living_square']=f_lsqr
    except:
        print('For cleaning ш. Варшавское, д. 144, к. 2 - ', sys.exc_info()[0])
        #7929586     ул. Флотская, д. 13, к. 3  1975.0     17  1МГ601   
    try:
        dtf.loc[7929586, 'living_square']=dtf.loc[7929614, 'living_square']
        #print(dtf.loc[7929586, 'living_square'])
        dtf.loc[7742610, 'living_square']=dtf.loc[7552321, 'living_square'] #г. Зеленоград, д. 815  1974.0      9   
    except:
        print('For cleaning г. Зеленоград, д. 815 error - ', sys.exc_info()[0])
    try:
        #Moscow spec - this house 9068616 from Tomsk!!! And with error living square
        
        dtf.drop([9068616], inplace=True)
        dtf.drop([8033016], inplace=True) #'МНОГОЭТАЖНАЯ НАДЗЕМНАЯ ОТКРЫТАЯ АВТОСТОЯНКА НА 100 МАШИНОМЕСТ'
        
        dtf.drop([9084016], inplace=True) # деревянный дом 321 этаж и жилой площадью млн. кв. м.
    except:
        print('For cleaning special Moscow error - ', sys.exc_info()[0])
        
    dtf.floors=pd.to_numeric(dtf.floors, errors='coerce')
    dtf.year=pd.to_numeric(dtf.year, errors='coerce')
    dtf.entrance=pd.to_numeric(dtf.entrance, errors='coerce')
    dtf.floors[dtf.floors>100]=0

    return dtf