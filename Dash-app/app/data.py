import firebirdsql
import pandas as pd
from datetime import datetime

# Установка соединения с базой данных
con = firebirdsql.connect(
       host='', database='',
       user='', password=''
   )

# Создание курсора для выполнения запросов
cur = con.cursor()
   
# Получение данных о прродажах
# Выполнение SQL-запроса
cur.execute('''WITH shema AS
(
	SELECT  treatdate,
	        orderdet.orderno,
	        treat.rid,
	        treat.depnum,
	        wschema.speccode,
	        schcode,
	        orderdet.pcode,
	        orderdet.filial,
	        filials.shortname,
            orderdet.dcode,
	        doctor.fullname         AS dname,
	        clients.fullname        AS patient,
            clients.pol,
            clients.bdate,
	        kodoper,
	        schname,
	        schamount,
	        schcount,
	        treat.jid,
	        jname
	FROM orderdet
	JOIN wschema
	ON wschema.schid = orderdet.schcode
	LEFT JOIN (SELECT treatdate, orderno, rid, depnum, treat.jid, jname
FROM treat
         LEFT JOIN (SELECT agrid, jpersons.jname FROM jpagreement JOIN jpersons USING(JID)) AS jpagreement ON jpagreement.agrid = treat.jid) AS treat USING (orderno)
	JOIN doctor USING(dcode)
	JOIN clients USING(pcode)
	JOIN filials
	ON filials.filid = orderdet.filial
	AND orderdet.filial IN (11, 12)
 	AND treat.treatdate BETWEEN '2023-01-01 00:00:00' AND CAST('Yesterday' AS DATE)
),  specialization AS
(
	SELECT  DISTINCT scode,
	        sname,
	        speciality.depnum,
	        depname,
	        CASE WHEN scode IN (1,62,78) THEN 'Терапия'
	             WHEN scode IN (2,63) THEN 'Неврология'
	             WHEN scode = 3 THEN 'Гастроэнтерология'
	             WHEN scode IN (4,49,990128511) THEN 'Эндокринология'
	             WHEN scode = 5 THEN 'Кардиология'
	             WHEN scode = 6 THEN 'Аллергология и иммунология'
	             WHEN scode = 7 THEN 'Педиатрия'
	             WHEN scode = 8 THEN 'Гомеопатия'
	             WHEN scode = 9 THEN 'Гематология'
	             WHEN scode IN (10,990027246) THEN 'Генетика'
	             WHEN scode IN (11,85) THEN 'Колопроктология'
	             WHEN scode IN (12,91) THEN 'Сердечно-сосудистая хирургия'
	             WHEN scode IN (13,92) THEN 'Нейрохирругия'
	             WHEN scode IN (14,94) THEN 'Онкология'
	             WHEN scode IN (15,90) THEN 'Травматология и ортопедия'
	             WHEN scode IN (17,64,86,100) THEN 'Акушерство и гинекология'
	             WHEN scode IN (18,65) THEN 'Дерматовенерология'
	             WHEN scode IN (19,66,87,990007755) THEN 'Урология'
	             WHEN scode IN (20,67,88) THEN 'Оториноларингология'
	             WHEN scode IN (21,68,89) THEN 'Офтальмология'
	             WHEN scode IN (22,93,990021488,990021490) THEN 'Пластическая хирургия'
	             WHEN scode = 23 THEN 'Остеопатия'
	             WHEN scode IN (24,990005431,990140661) THEN 'Психотерапия'
	             WHEN scode = 25 THEN 'Рефлексотерапия'
	             WHEN scode IN (26,70) THEN 'Ультразвуковая диагностика'
	             WHEN scode IN (27,71) THEN 'Функциональная диагностика'
	             WHEN scode IN (28,72,83) THEN 'Эндоскопия'
	             WHEN scode IN (990234644) THEN 'Клиническая лабораторная диагностика (ВМТ)'
                 WHEN scode IN (990010000000001, 29,73,104,990007401,990021175,990027240,990130828,990233120, 990245486,990245487,990245488,990252029,990010000000001) THEN 'Клиническая лабораторная диагностика (Прочее)'
	             WHEN scode IN (30,31,74,75) THEN 'Рентгенология'
                 WHEN scode IN (990007533) THEN 'Рентгенология (МРТ)'
                 WHEN scode IN (32) THEN 'Рентгенология (КТ)'
	             WHEN scode IN (33,69,80,81,82,16,84) THEN 'Хирургия'
	             WHEN scode IN (34,38,101,990130312,990135002,990135004,990152488) THEN 'Физиотерапия'
	             WHEN scode = 35 THEN 'Дневной стационар'
	             WHEN scode = 36 THEN 'Медицинский массаж'
	             WHEN scode = 39 THEN 'Лечебная физкультура и спортивная медицина'
	             WHEN scode = 40 THEN 'Эфферентная терапия'
	             WHEN scode IN (41,79) THEN 'Анестезиология-реаниматология'
	             WHEN scode IN (43,990027245) THEN 'Вакцинация'
	             WHEN scode = 44 THEN 'Детская кардиология'
	             WHEN scode = 45 THEN 'Детская онкология'
	             WHEN scode IN (46,96) THEN 'Детская урология-андрология'
	             WHEN scode IN (47,97) THEN 'Детская хирургия'
	             WHEN scode IN (48,990262643) THEN 'Детская эндокринология'
	             WHEN scode = 50 THEN 'Инфекционные болезни'
	             WHEN scode IN (51,95) THEN 'Нефрология'
	             WHEN scode IN (52,76,990135001,990153657) THEN 'Психиатрия-наркология'
	             WHEN scode = 53 THEN 'Пульмонология'
	             WHEN scode = 54 THEN 'Ревматология'
	             WHEN scode IN (55,990023598,990023598) THEN 'Сексология'
	             WHEN scode IN (56,98,990027388) THEN 'Трансфузиология'
	             WHEN scode IN (57,99) THEN 'Челюстно-лицевая хирургия'
	             WHEN scode IN (103,990130163,990135003,990135005) THEN 'Косметология'
	             WHEN scode = 990005180 THEN 'Диетология'
	             WHEN scode IN (990005621,990043191) THEN 'Стоматология общей практики'
	             WHEN scode IN (990027247,990027277) THEN 'Мануальная терапия'
	             WHEN scode = 990027367 THEN 'Психиатрия'
	             WHEN scode = 990129263 THEN 'Профпатология'
	             WHEN scode = 990153658 THEN 'Торакальная хирургия'
	             WHEN scode = 990005147 THEN 'Судебно-медицинская экспертиза'
	             WHEN scode IN (77,990000312) THEN 'Сестринское дело'  ELSE 'Прочее' END AS specname
	FROM speciality
	JOIN departments USING(depnum)
)

SELECT  treatdate,
        shema.shortname,
        dname,
        patient,
        pol,
        bdate,
        kodoper,
        schname,
        scode,
        sname AS sname1,
        specname,
        LOWER(depname)                                                                     AS depname,
        CASE WHEN scode IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,33,34,35,36,38,39,40,41,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,71,101,102,103,990005147,990005180,990005431,990023598,990027367,990027277,990130163,990130312,990135001,990140661,990152488,990153658,990262643,990000312,990129263) THEN 'Поликлиника'
             WHEN scode BETWEEN 62 AND 76 AND scode IN (990005621,990128511,990129263,990130828,990153657) THEN 'Медосмотр'
             WHEN scode IN (78, 79,86,90,87,93,85,91,80,94,88,92,82,84,990000313,990007764,990027368,990027389,990027389) THEN 'Стационар'
             WHEN scode = 100 THEN 'Вспомагательные репродуктивные технологии (ВРТ)'
             WHEN scode = 990100400 THEN 'Телемедицинские услуги'
             WHEN scode IN (29,73,990010000000001,990233120,990234644,990245486,990245487,990245488,990252029, 990027240) THEN 'Лаборатория'
             WHEN scode = 1 THEN 'Поликлиника'
             WHEN scode IN (990007533,32,31) THEN 'Лучевая диагностика'  ELSE 'Прочее' END AS sname,
        rooms.rnum,
        jname,
        schamount,
        schcount
FROM shema
         LEFT JOIN rooms
                   ON rooms.rid = shema.rid
         LEFT JOIN specialization
                   ON specialization.scode = shema.speccode
ORDER BY treatdate, shortname, dname''')
   # Получение результатов запроса
results = cur.fetchall()
   
   # Закрытие соединения и освобождение ресурсов
cur.close()
con.close()

# таблица справочник клиентов
sales_df = pd.DataFrame(results, columns=['treatdate', 'shortname', 'dname', 'patient', 'pol', 'bdate', 'kodoper', 'schname', 'scode', 'sname1', 'specname', 'depname', 'sname', 'rname', 'jname', 'schamount', 'schcount'])

sales_df['treatdate'] = pd.to_datetime(sales_df['treatdate'])
sales_df['bdate'] = pd.to_datetime(sales_df['bdate'])
sales_df['month'] = sales_df['treatdate'].dt.month
sales_df['age'] = sales_df['treatdate'].dt.year - sales_df['bdate'].dt.year - ((sales_df['treatdate'].dt.month * 100 + sales_df['treatdate'].dt.day) < (sales_df['bdate'].dt.month * 100 + sales_df['bdate'].dt.day))
sales_df['year'] = sales_df['treatdate'].dt.year
# добавляем столбец с группами в датафрейм
def age_group (x):
    if x['age'] < 17:
        return '0-17'
    elif x['age'] < 25:
        return '18-24'
    elif x['age'] < 35:
        return '25-34'
    elif x['age'] < 45:
        return '35-44'
    elif x['age'] < 55:
        return '45-64'
    else:
        return '65 +'
    
sales_df['age_groups'] = sales_df.apply(age_group, axis = 1)

# добавляем столбец с группами в датафрейм
def month_text (x):
    if x['month'] == 1:
        return 'Январь'
    elif x['month'] == 2:
        return 'Февраль'
    elif x['month'] == 3:
        return 'Март'
    elif x['month'] == 4:
        return 'Апрель'
    elif x['month'] == 5:
        return 'Май'
    elif x['month'] == 6:
        return 'Июнь'
    elif x['month'] == 7:
        return 'Июль'
    elif x['month'] == 8:
        return 'Август'
    elif x['month'] == 9:
        return 'Сентябрь'
    elif x['month'] == 10:
        return 'Октябрь'
    elif x['month'] == 11:
        return 'Ноябрь'
    else:
        return 'Декабрь'
    
sales_df['month_text'] = sales_df.apply(month_text, axis = 1)
sales_df.to_csv('app/data/sales.csv', encoding='utf-8', sep=',')

current_datetime = datetime.now()
print(f'запрос выполнен успешно {current_datetime} файл сохраннен в папку /data/sales.csv ')
