from symtable import Symbol
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash_table.Format import Format, Scheme, Symbol
import pandas as pd
from dash import dash_table
import plotly.graph_objects as go
from flask import Flask
import dash_auth
from dash_auth import BasicAuth
import sqlite3

server = Flask(__name__)
# Создаем приложение Dash
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.MINTY])

df = pd.read_csv('app/data/sales.csv', encoding='utf-8', sep=',')
df['treatdate'] = pd.to_datetime(df['treatdate'])
df = df.sort_values('treatdate')
df = df.drop(df.columns[0], axis=1)
df['sname'] = df['sname'].str.strip()

df_until = pd.read_csv('app/data/df_until.csv')
df_until['ORDERDATE'] = pd.to_datetime(df_until['ORDERDATE'])
df_until = df_until.sort_values('ORDERDATE')

plan_df = pd.read_csv('app/data/Plan.csv')
plan_df['DATES'] = pd.to_datetime(plan_df['date'])

# app = dash.Dash(__name__, 
#                 external_stylesheets=[dbc.themes.MINTY])
app.title = 'План-фактный анализ'

USER_PWD = {
    'Test': 'Test',
}
BasicAuth(app, USER_PWD)

# conn = sqlite3.connect('app/data/UserAccPlan.db')
# cur = conn.cursor()
# cur.execute('SELECT login, password FROM UserAcсess')
# conn.commit()
# UserAuth = cur.fetchall()
# cur.close()
# conn.close()
# USER_PWD = {login: password for login, password in UserAuth}

BasicAuth(app, USER_PWD)

# последний месяц в данных
current_month = df['month_text'][df['month'] == df['month'].max()].iloc[0]

# Список уникальных месяцев
available_months = df['month_text'].unique()

# Список уникальных подразделений
available_department = df['sname'].unique()

# Список уникальных филиалов
available_filial = df['shortname'].unique()

# FUNCS ---------------------------------------------------------------

def sales_group(data, month, filial, department, specialization, index):
    # Сначала фильтруем данные по месяцу
    df_filtered = data[data['month_text'] == month]
    
    # Затем, если выбран филиал, фильтруем по филиалу
    if filial:
        df_filtered = df_filtered[df_filtered['shortname'] == filial]
    
    # Затем, если выбран департамент, фильтруем по департаменту
    if department:
        df_filtered = df_filtered[df_filtered['sname'] == department]
        
    # И, наконец, если выбрана специализация, фильтруем по специализации
    if specialization:
        df_filtered = df_filtered[df_filtered['specname'] == specialization]

    # Группируем данные и возвращаем результат
    sales_group_pivot = df_filtered.pivot_table(
        index=index,
        values='schamount',
        aggfunc='sum'
    )
    sales_group_df = sales_group_pivot.reset_index()
    data = sales_group_df.to_dict('records')

    return data

def plan_filtred_month(month, filial, department):
    if department:
        plan_filtred_df = plan_df['plan'][(plan_df['month_text'] == month) & (plan_df['shortname'] == filial) & (plan_df['sname'] == department)].sum()
    else:
        plan_filtred_df = plan_df['plan'][(plan_df['month_text'] == month) & (plan_df['shortname'] == filial)].sum()
    
    return plan_filtred_df

def indicators(month, filial, data, data_plan, department):
        # подготавлием данные с учетом месяца и департамента
        if not data.empty:
                current_month = data['month'][(data['month_text'] == month)].max()
        if current_month == 1:
            last_month = 12
        else:
            last_month = current_month - 1
        
        if department:
                data_df = data[(data['month_text'] == month) & (data['shortname'] == filial) & (data['sname'] == department)]
                filtered_data_plan = data_plan[(data_plan['month_text'] == month) & (data_plan['shortname'] == filial) & (data_plan['sname'] == department)]
                last_month_data = data[(data['month'] == last_month) & (data['shortname'] == filial) & (data['sname'] == department)]
        else:
                filtered_data_plan = data_plan[(data_plan['month_text'] == month) & (data_plan['shortname'] == filial)]
                data_df = data[(data['month_text'] == month) & (data['shortname'] == filial)]
                last_month_data = data[(data['month'] == last_month) & (data['shortname'] == filial)]
        # считаем план
        plan = filtered_data_plan['plan'].sum()
        
        # устававлиаем rang на шкале графика  
        plan_range_bad = plan - (plan * 0.1)
        plan_range_good = plan - (plan * 0.07)
    
        revenue = data_df['schamount'].sum()
        delta = last_month_data['schamount'].sum()
        
        # Рассчитываем Run Rate
        if month and not data_df.empty:
            total_amount = data_df['schamount'].sum()
            unique_days = data_df['treatdate'].dt.day.nunique()
            days_in_month = data_df['treatdate'].dt.daysinmonth.iloc[0]
            run_rate = (total_amount / unique_days * days_in_month).round()
            run_rate_plan = (run_rate / plan * 100).round()
            plan_progress = revenue / plan * 100
        else:
            run_rate = 0
            run_rate_plan = 0
            plan_progress = 0
    
        # Если есть данные выводим графики
        fig = go.Figure()
        if month in data_df['month_text'].unique() and filial in data_df['shortname'].unique():
                
                # выводим график с текущей выручкой
                fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = revenue,
                number={'prefix': '₽',
                        'font': {'size': 26,
                        'color': '#022424',
                                },
                        },
                gauge = {
                        'axis': {'range': [None, plan + 10e6], 'tick0': 10e6, 'dtick': 15e6, 'tickprefix': '₽',},
                        'bar': {'color': "#63DFDC"},
                        'steps' : [
                                {'range': [0, plan_range_bad], 'color': "white"},
                                {'range': [plan_range_bad, plan_range_good], 'color': "#DCF3F3"},
                                {'range': [plan_range_good, plan], 'color': "#00BFB2"}],
                        'threshold': {'line': {'color': "#9C7650", 'width': 2}, 'thickness': 1, 'value': plan}},
                title = {'text': "Текущая выручка<br><span style='font-size:0.8em;color:#27736B'></span>"},
                
                title_font = {'color': "#27736B", 'size':14},
                domain = {'row': 0, 'column': 0}
                ))

                # выводим график сравнения выручки с прошлым месяцем
                fig.add_trace(go.Indicator(
                value = revenue,
                delta={'position': 'top',
                       'reference': delta,
                       'increasing': {'color': "#63DFDC"},
                       'decreasing': {'color': "#731D2C"},
                       'relative': False,
                       'prefix': '₽',
                       'font': {'size': 18,},
                        },
                gauge = {
                        # 'shape': "bullet",
                        'axis' : {'range': [None, plan + 10e6], 'visible': True, 'tick0': 10e6, 'dtick': 15e6, 'tickprefix': '₽',},
                        'bar': {'color': "#63DFDC"},
                        'steps' : [
                                {'range': [0, delta], 'color': "#27736B"}],
                        'threshold': {'line': {'color': "#9C7650", 'width': 2}, 'thickness': 1, 'value': plan}},
                title = {"text": "Текущая выручка<br><span style='font-size:0.8em;color:#27736B'>по отношению к выручке прошлого месяца</span><br><span style='font-size:0.8em;color:#27736B'></span>"},
                title_font = {'color': "#27736B", 'size': 12},
                domain = {'row': 0, 'column': 1}))
                fig.update_layout(
                    grid = {'rows': 1, 'columns': 2, 'pattern': "independent"},
                    margin=dict(l=40, r=40, t=40, b=0),
                    template = {'data' : {'indicator': [{'mode' : "delta+gauge",
                                                         'delta' : {'reference': plan}}
                                                        ]}
                                },
                    width=480,
                    height=160
                )
        else:
                # Создаем пустой график или добавляем текст об отсутствии данных
                fig.add_trace(
                        go.Indicator(
                                mode='number',
                                value= 0,
                                title={'text': 'Нет данных',
                                'font': {'size': 12
                                                },
                                },
                                number={'prefix': '₽',
                                        'font': {'size': 18,
                                                },
                                        },
                                domain={'y': [0, 0.7], 'x': [0.25, 0.75]},
                        )
                ) 
        return fig, run_rate, run_rate_plan, plan_progress

def gropped_filial_amount_period(data, filial, period):
    x = sorted(data[data['shortname'] == filial].groupby(pd.Grouper(key='treatdate', freq=period)).agg(
        {'schamount': 'sum'}).reset_index()["treatdate"].unique())
    
    y = data[data['shortname'] == filial].groupby(pd.Grouper(key='treatdate', freq=period)).agg(
        {'schamount': 'sum'}).reset_index()['schamount']
    
    return x, y

kpi_rus = {
    "schamount": "Выручка",
    "specname": "Специализация",
    "dname": "Полное имя врача"
}

data_specialization = sales_group(df, current_month, '', '', '', 'specname')
data_specialization_df = pd.DataFrame(data_specialization)

data_doctor = sales_group(df, current_month, '', '', '', 'dname')
data_doctor_df = pd.DataFrame(data_doctor)

initial_active_cell = None

def data_bars(df, column):
    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    ranges = [
        ((df[column].max() - df[column].min()) * i) + df[column].min()
        for i in bounds
    ]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        max_bound_percentage = bounds[i] * 100
        styles.append({
            'if': {
                'filter_query': (
                    '{{{column}}} >= {min_bound}' +
                    (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                'column_id': column
            },
            'background': (
                """
                    linear-gradient(90deg,
                    #E6EFEF 0%,
                    #45AEB5 {max_bound_percentage}%,
                    white {max_bound_percentage}%,
                    white 100%)
                """.format(max_bound_percentage=max_bound_percentage)
            ),
            'paddingBottom': 2,
            'paddingTop': 2
        })

    return styles

def dynamic_by_year(data, old_data, data_plan, department):
    
    if department:
        data = data[data['sname']== department]
        old_data = old_data[old_data['department'] == department]
        data_plan = data_plan[data_plan['sname'] == department]
    
    sales_old_pivot = old_data.pivot_table(
        index=['month', 'month_text'],
        values='SCHAMOUNT',
        columns='year', 
        aggfunc='sum'
    ).fillna(0)
    sales_old_month = sales_old_pivot.reset_index()

    sales_pivot = data.pivot_table(
        index=['month', 'month_text'],
        values='schamount',
        columns='shortname',  
        aggfunc='sum'
    ).fillna(0)

    sales_month = sales_pivot.reset_index()

    sales_month = sales_old_month.merge(
        sales_month,
        on='month',
    ).drop_duplicates()
    
    sales_month['ПЕРСОНА-МЕД'] = sales_month[2023] + sales_month['ПЕРСОНА-МЕД']

    cols = [7, 8]
    sales_month.drop(sales_month.columns[cols], axis=1, inplace=True)
    sales_month = sales_month.rename(columns={'month_text_x': 'month_text', 
                                            2018: '2018', 2019: '2019', 2020: '2020', 2021: '2021', 2022: '2022'})

    plan_pivot = data_plan.pivot_table(index=['month', 'month_text'],
                                    columns='shortname',
                                    values='plan',
                                    aggfunc='sum').fillna(0)
    plan_month_df = plan_pivot.reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plan_month_df['month_text'],
                            y=plan_month_df['ПЕРСОНА-МЕД'],
                            mode='lines',
                            fill='tozeroy',
                            line_color='#DCF2F0',
                            line=dict(width=1),
                            name='план ПЕРСОНА-МЕД'))
    fig.add_trace(go.Scatter(x=plan_month_df['month_text'],
                            y=plan_month_df['ВМТ 2'],
                            mode='lines',
                            fill='tozeroy',
                            line_color='#8DB7A5',
                            line=dict(width=1),
                            name='план ВМТ 2'))
    fig.add_trace(go.Scatter(x=sales_month['month_text'],
                            y=sales_month['2022'],
                            mode='lines+markers',
                            line=dict(color='#BF8049'),
                            name='2022'))
    fig.add_trace(go.Scatter(x=sales_month['month_text'],
                            y=sales_month['2021'],
                            mode='lines+markers',
                            line=dict(color='#49A69C'),
                            name='2021'))
    fig.add_trace(go.Scatter(x=sales_month['month_text'],
                            y=sales_month['2020'],
                            mode='lines+markers',
                            line=dict(color='lightskyblue'),
                            name='2020'))
    fig.add_trace(go.Scatter(x=sales_month['month_text'],
                            y=sales_month['2019'],
                            mode='lines+markers',
                            line=dict(color='limegreen'),
                            name='2019'))
    fig.add_trace(go.Scatter(x=sales_month['month_text'],
                            y=sales_month['ПЕРСОНА-МЕД'],
                            mode='lines+markers',
                            line=dict(color='#63DFDC'),
                            name='ПЕРСОНА-МЕД 2023'))
    fig.add_trace(go.Scatter(x=sales_month['month_text'],
                            y=sales_month['ВМТ 2'],
                            mode='lines+markers',
                            line=dict(color='#1C5959'),
                            name='ВМТ 2 2023'))
    fig.update_layout(#title='Динамика выручки по месяцам',
                    xaxis_title='Месяц',
                    yaxis_title='Выручка, руб.',
                    hovermode='x',
                    margin=dict(l=15, r=15, t=50, b=60),
                    plot_bgcolor='white',
                    xaxis=dict(
                        showgrid=False,
                        gridcolor='gray'),
                    yaxis=dict(
                        showgrid=False,
                        gridcolor='gray'),
                    autosize=True,
                    #   width=750,
                    height=340
                    )

    fig.update_traces(hoverinfo='all', hovertemplate='Месяц: %{x}<br>Выручка: %{y}')

    fig.update_traces(
        line=dict(width=3),  # Устанавливаем толщину линии равной 3
        selector=dict(name='ПЕРСОНА-МЕД 2023')  # Указываем имя трассы, для которой применяем изменения
    )
    fig.update_traces(
        line=dict(width=3),  # Устанавливаем толщину линии равной 3
        selector=dict(name='ВМТ 2 2023')  # Указываем имя трассы, для которой применяем изменения
    )
    fig.update_traces(
        line=dict(width=1),  # Устанавливаем толщину линии равной 1
        selector=dict(name='2022')  # Указываем имя трассы, для которой применяем изменения
    )
    fig.update_traces(
        line=dict(width=1),  # Устанавливаем толщину линии равной 1
        selector=dict(name='2021')  # Указываем имя трассы, для которой применяем изменения
    )
    fig.update_traces(
        line=dict(width=1),  # Устанавливаем толщину линии равной 1
        selector=dict(name='2020')  # Указываем имя трассы, для которой применяем изменения
    )
    fig.update_traces(
        line=dict(width=1),  # Устанавливаем толщину линии равной 1
        selector=dict(name='2019')  # Указываем имя трассы, для которой применяем изменения
    )
    
    return fig

# GRAPHS --------------------------------------------------------

fig1= go.Figure()
fig1.add_trace(go.Scatter(x= gropped_filial_amount_period(df, 'ПЕРСОНА-МЕД', '1D')[0],
                        y= gropped_filial_amount_period(df, 'ПЕРСОНА-МЕД', '1D')[1],
                        mode='lines+markers', # Выводим линию и маркеры
                        fill='tozeroy',
                        text=gropped_filial_amount_period(df, 'ПЕРСОНА-МЕД', '1D')[1].apply(lambda x: f'{x:,.0f}₽'),
                        textposition='top center',
                        name='ПЕРСОНА-МЕД')) # Присваиваем имя 
fig1.add_trace(go.Scatter(x= gropped_filial_amount_period(df, 'ВМТ 2', '1D')[0],
                        y= gropped_filial_amount_period(df, 'ВМТ 2', '1D')[1],
                        mode='lines+markers',
                        fill='tozeroy', 
                        name='ВМТ 2'))

fig1.update_layout(#title='Динамика выручки по месяцам', # Название графика
                legend_orientation='h', # Устанавливасем горизонтальную ориентацию легенды
                legend=dict(x=.0, xanchor="left"), # Меняем положение легенды на центрально
                xaxis_title='Дата', # Устанавливаем название оси x
                yaxis_title='Выручка, руб.', # Устанавливаем название оси y
                hovermode='x',
                margin=dict(l=5, r=5, t=5, b=5),  # Устанавливаем отступы
                plot_bgcolor='white', # Устанавливаем белый цвет заднего фона
                    xaxis=dict(
                        showgrid=False,  # Отображаем сетку по оси X
                        gridcolor='gray'),  # Устанавливаем цвет сетки по оси X
                    yaxis=dict(
                        showgrid=False,  # Отображаем сетку по оси Y
                        gridcolor='gray'),  # Устанавливаем цвет сетки по оси Y
                autosize=False,  # Отключаем автоматическое изменение размеров графика
                # width=600,  # Устанавливаем ширину графика
                height=270,  # Устанавливаем высоту графика 
                ) 
fig1.update_traces(hoverinfo='all', hovertemplate='Дата: %{x}<br>Выручка: %{y}')
fig1.update_traces(
    line=dict(color='#1C5959'),  # Устанавливаем цвет линии для "ВМТ 2"
    selector=dict(name='ВМТ 2')  # Указываем имя трассы, для которой применяем изменения
)
fig1.update_traces(
    line=dict(color='#63DFDC'),  # Устанавливаем цвет линии для "ВМТ 1"
    selector=dict(name='ПЕРСОНА-МЕД')  # Указываем имя трассы, для которой применяем изменения
)
fig1.update_traces(
    line=dict(width=1),  # Устанавливаем толщину линии
    selector=dict(name='ВМТ 2')  # Указываем имя трассы, для которой применяем изменения
)
fig1.update_traces(
    line=dict(width=1),  # Устанавливаем толщину линии
    selector=dict(name='ПЕРСОНА-МЕД')  # Указываем имя трассы, для которой применяем изменения
)

# индикаторы по ВМТ 1
fig2 = indicators(current_month, 'ПЕРСОНА-МЕД', df, plan_df, '')[0]

# индикаторы по ВМТ 2
fig3 = indicators(current_month, 'ВМТ 2', df, plan_df, '')[0]

fig7 = dynamic_by_year(df, df_until, plan_df, '')

# MARKUP ELEMENTS -----------------------------------------------------------------------------------

plan_label = html.Div([
    dbc.Alert([
        html.H4([f"План WMT 1 на {current_month}", 
                dbc.Badge(f"{plan_filtred_month(current_month, 'ПЕРСОНА-МЕД', ''):,.0f} ₽",
                        color="info",  
                        className="ms-1")]), 
        ], color="warning"
            )
])

plan_label2 = html.Div([
    dbc.Alert([
        html.H4([f"План WMT 2 на {current_month}", 
                dbc.Badge(f"{plan_filtred_month(current_month, 'ВМТ 2', ''):,.0f} ₽",
                        color="info",  
                        className="ms-1")]), 
        ], color="warning"
            )
])

run_rate_wmt1 = dbc.Alert([
    html.P(f"Прогноз выручки и выполнения плана на конец месяца", className="alert-heading",),
    dbc.Placeholder(size="xs", className="me-1 mt-1 w-100"),
    html.H5([f"{(indicators(current_month, 'ПЕРСОНА-МЕД', df, plan_df, '')[1]):,.0f} ₽", 
                dbc.Badge(f"{(indicators(current_month, 'ПЕРСОНА-МЕД', df, plan_df, '')[2]):,.0f} %",
                        color="info",  
                        className="ms-1")]),
    ], color="light")

run_rate_wmt2 = dbc.Alert([
    html.P(f"Прогноз выручки и выполнения плана на конец месяца", className="alert-heading",),
    dbc.Placeholder(size="xs", className="me-1 mt-1 w-100"),
    html.H5([f"{(indicators(current_month, 'ВМТ 2', df, plan_df, '')[1]):,.0f} ₽", 
                dbc.Badge(f"{(indicators(current_month, 'ВМТ 2', df, plan_df, '')[2]):,.0f} %",
                        color="info",  
                        className="ms-1")]),
    ], color="light")

plan_progress_wmt1 = dbc.Alert([
    html.P(f"Текущий % выполнения плана", className="alert-heading",),
    dbc.Placeholder(size="xs", className="me-1 mt-1 w-100"),
    html.H1([dbc.Badge(f"{(indicators(current_month, 'ПЕРСОНА-МЕД', df, plan_df, '')[3]):,.0f} %",
                        color="info",  
                        className="ms-5")]),
    ], color="light")

plan_progress_wmt2 = dbc.Alert([
    html.P(f"Текущий % выполнения плана", className="alert-heading",),
    dbc.Placeholder(size="xs", className="me-1 mt-1 w-100"),
    html.H1([dbc.Badge(f"{(indicators(current_month, 'ВМТ 2', df, plan_df, '')[3]):,.0f} %",
                        color="info",  
                        className="ms-5")]),
    ], color="light")


# LAYOUT-----------------------------------------------------------------------

# Создаем макет приложения
app.layout = dbc.Container([
    dbc.CardBody([
        # SIDEBAR
        dbc.Row([
            dbc.Col([
                html.Br(),
                html.Img(src='https://cabinet.wmtmed.ru/img/logo_wmt/logo.svg',
                         style={"width": "12rem",}),
                html.Br(),
                html.Br(),
                html.Br(),
                html.P(children="Месяц",
                       style={'color': '#ffffff',
                              "width": "12rem",
                              'position': 'sticky'
                              },
                       className="header-description"
                       ),
                dcc.Dropdown(
                    id='month_dropdown',
                    options=[{'label': month, 'value': month} for month in available_months],
                    placeholder='Выберите месяц',
                    value=current_month, # Устанавливаем значение по умолчанию
                    style={
                           "width": "12rem",
                           }),
                html.Br(),
                html.P(children="Подразделение",
                       style={'color': '#ffffff',
                              "width": "12rem",},
                       className="header-description"),
                dcc.Dropdown(id='departments_dropdown',
                             options=[{'label': sname, 'value': sname} for sname in available_department],
                             placeholder='Выберите подразделение',
                             style={"width": "12rem",}
                             ),
                html.Br(),
                html.P(children="Филиал",
                       style={'color': '#ffffff',
                              "width": "12rem",},
                       className="header-description"),
                dcc.Dropdown(
                    id='filial_dropdown',
                    options=[{'label': shortname, 'value': shortname} for shortname in available_filial],
                    placeholder='Выберите филиал',
                    style={"width": "12rem",} 
                    ),
                dbc.CardBody([
                    html.P("© 2023 КЛИНИКА WMT", className="card-text"),
                    html.P("created by Alexander Sutyagin", className="card-text")
                ],style={
                         'margin-top': '100%',
                         'font-size': '0.8em',
                         'text-align':'center',
                         'color': '#27736B'}),
            ], width=1, 
               style = {'background-color': '#47B1B8',
                        'height': 'calc(100% - 4rem)',
                        'width': "15rem",
                        'border-style': 'solid',
                        'border-width':'1px', 
                        'border-color': '#47B1B8',
                        'border-radius': '7px',
                        'position': 'fixed',
                        'margin-top': '2rem',
                        }),
            # HEADER
            dbc.Col([
                html.H1(
                    children="План-фактный анализ",
                    style={'text-align':'center',
                           'color': '#444444',}
                ),
                html.Br(),
                dbc.Alert(["План-фактный анализ позволяет оценить состояние и изминениние текущей выручки по филиалам, "
                        "по отношению к прошлому месяцу, прогноз (Run Rate) для месяца "
                        "на основе продаж за день по отношению к плану за месяц и текущее выполнение плана " 
                        "за установленный период."], 
                        color="primary",),
                # INDICATORS
                dbc.Row([
                    dbc.Col([
                      dbc.CardBody([
                          dbc.Row([
                              dbc.Col([
                                  html.Label(id='plan-label',
                                             children=plan_label,),
                                   html.P("Динамика выручки за месяц по филиалу WMT 1", className="display-6", 
                                          style={'font-size': 21,
                                                 'text-align': 'left',
                                                 'color': '#277273',},),
                              ]),
                          ]),
                          dbc.Row([
                              dbc.Col([
                                  dcc.Graph(id='delta-indicator-1',
                                            config={'displayModeBar': False}, 
                                            figure=fig2) 
                                  ])
                              ]),
                          dbc.Row([
                              dbc.Col([
                                  html.Label(id='plan-progress-wmt1-label', children=plan_progress_wmt1),
                              ]),
                              dbc.Col([
                                  html.Label(id='runratewmt1-label',
                                             children=run_rate_wmt1,),   
                              ]),
                          ])
                          ])
                      ], width=True,
                            align="center",
                            style ={'border-style': 'solid',
                                    'border-width':'1px',
                                    'border-color': '#ffffff',
                                    'border-radius': '7px',
                                    'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)',
                                    'padding': '10px',
                                    "margin": "1rem",}),
                    dbc.Col([
                      dbc.CardBody([
                        html.Label(id='plan-label2',
                                   children=plan_label2,
                        ),
                        html.P("Динамика выручки за месяц по филиалу WMT 2", className="display-6",
                               style={'font-size': 21,
                                      'text-align': 'left',
                                      'color': '#277273',},),
                          dbc.Row([
                              dbc.Col([
                                  dcc.Graph(id='delta-indicator-2',
                                            config={'displayModeBar': False}, 
                                            figure=fig3) 
                                  ])
                              ]),
                          dbc.Row([
                              dbc.Col([
                                  html.Label(id='plan-progress-wmt2-label', children=plan_progress_wmt2),
                              ]),
                              dbc.Col([
                                  html.Label(id='runratewmt2-label',
                                             children=run_rate_wmt2,),   
                              ]),
                          ])
                        ])
                      ], width=True,
                            align="center",
                       style ={'border-style': 'solid',
                               'border-width':'1px',
                               'border-color': '#ffffff',
                               'border-radius': '7px',
                               'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)',
                               'padding': '10px',
                               "margin": "1rem",}
                       )
                ]),
                # DYNAMiCS
                dbc.Tabs([
                    dbc.Tab([
                        dbc.Row([
                            dbc.Col([
                                dbc.CardBody([
                                    html.P("Динамика выручки за месяц", className="display-6",
                                           style={'font-size': 21,
                                                  'text-align': 'left',
                                                  'color': '#277273',},
                                           ),
                                    dcc.Graph(id='graph-1',
                                              config={'displayModeBar': False},
                                              figure=fig1
                                              )
                                    ]) 
                                ], width=True,
                                    align="center",
                                    style ={
                                        'height': "23rem",
                                        'border-style': 'solid',
                                        'border-width':'1px',
                                        'border-color': '#ffffff',
                                        'border-radius': '7px',
                                        'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)',
                                        'padding': '10px',
                                        "margin": "1rem",}
                                    ),
                            ]),
                        ], label="Динамика выручки за месяц"),
                    dbc.Tab([
                        dbc.Row([
                            dbc.Col([
                                dbc.CardBody([
                                    html.P("Динамика выручки по отношению к прошлым годам",
                                           style={'font-size': 21,
                                                  'text-align': 'left',
                                                  'color': '#277273',},),
                                    html.P("На фоне отображена динамика плана за последний год", className="display-6",
                                           style={'font-size': 16,
                                                  'text-align': 'left',}),
                                    dcc.Graph(
                                        id='graph-2',
                                        config={'displayModeBar': False},
                                        figure=fig7
                                        )
                                    ]) 
                                ], width=True,
                                    align="center",
                                    style ={'border-style': 'solid',
                                            'border-width':'1px',
                                            'border-color': '#ffffff',
                                            'border-radius': '7px',
                                            'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)',
                                            'padding': '10px',
                                            "margin": "1rem",}
                                    )
                            ])
                        ], label="Динамика выручки по отношению к прошлым годам")
                    ], id="tabs",
                         ),
                dbc.Tabs([
                    dbc.Tab([
                        dbc.Row([
                            dbc.Col([
                                dbc.CardBody([
                                    html.P("Выручка по специализациям",
                                           style={'font-size': 21,
                                                  'text-align': 'left',
                                                  'color': '#277273',},),
                                    html.P("Можно изменять сортировку с помощью заголовков столбцов", className="display-7"),
                                    dash_table.DataTable( 
                                                         id='specialization-sales',
                                                         sort_action='native',
                                                         active_cell = initial_active_cell,
                                                         filter_action="native",
                                                         filter_options={"placeholder_text": "поиск", "case": "insensitive", "applicable filter": "sensitive"},
                                                         columns=[{'name': kpi_rus[i], 'id': i, 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed,
                                                                                                                                    symbol=Symbol.yes,
                                                                                                                                    symbol_prefix=u'₽').group(True)} 
                                                                  for i in ["specname", "schamount"]
                                                                  ],
                                                         style_data_conditional=(
                                                             data_bars(data_specialization_df,'schamount')
                                                             ),
                                                         data=data_specialization,
                                                         style_cell={
                                                             'width': '100px',
                                                             'minWidth': '100px',
                                                             'maxWidth': '100px',
                                                             'overflow': 'hidden',
                                                             'textOverflow': 'ellipsis',
                                                             'text_align': 'left',
                                                             'font-size': '14px',
                                                             'color': '#222222',
                                                             },
                                                         style_header={
                                                             'backgroundColor': 'white',
                                                             'fontWeight': 'bold',
                                                             'text-align': 'center',
                                                             'font-size': '14px',
                                                             },
                                                         page_action='none',
                                                         style_table={'height': '20rem', 'overflowY': 'auto'}
                                                         ),
                                    ])
                                ], width=True,
                                    align="center",
                                    style ={'border-style': 'solid',
                                            'border-width':'1px',
                                            'border-color': '#ffffff',
                                            'border-radius': '7px',
                                            'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)',
                                            'padding': '10px',
                                            "margin": "1rem",}
                                    )
                            ])
                        ], label="Выручка по специализациям"
                            ),
                    dbc.Tab([
                        dbc.Row([
                            dbc.Col([
                                dbc.CardBody([
                                    html.P("Выручка по врачу",
                                           style={'font-size': 21,
                                                  'text-align': 'left',
                                                  'color': '#277273',},),
                                    html.P("Можно изменять сортировку с помощью заголовков столбцов", className="display-7"),
                                    dash_table.DataTable(
                                        id='doctor-sales',
                                        sort_action='native',
                                        filter_action="native",
                                        filter_options={"placeholder_text": "поиск", "case": "insensitive", "applicable filter": "insensitive"},
                                        columns=[{'name': kpi_rus[i], 'id': i, 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed,
                                                                                                            symbol=Symbol.yes,
                                                                                                            symbol_prefix=u'₽').group(True)} 
                                                 for i in ["dname", "schamount"]
                                                 ],
                                        style_data_conditional=(
                                            data_bars(data_doctor_df,'schamount')
                                            ),
                                        data=data_doctor,
                                        style_cell={
                                            'width': '110px',
                                            'minWidth': '100px',
                                            'maxWidth': '110px',
                                            'overflow': 'hidden',
                                            'textOverflow': 'ellipsis',
                                            'text_align': 'left',
                                            'font-size': '14px',
                                            'color': '#222222',
                                        },
                                        style_header={
                                            'backgroundColor': 'white',
                                            'fontWeight': 'bold',
                                            'text-align': 'center',
                                            'font-size': '14px',
                                            },
                                        page_action='none',
                                        style_table={'height': '20rem', 'overflowY': 'auto'}
                                        ), 
                                    ])
                                ], width=True,
                                    align="center",
                                    style ={'border-style': 'solid',
                                            'border-width':'1px',
                                            'border-color': '#ffffff',
                                            'border-radius': '7px',
                                            'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)',
                                            'padding': '10px',
                                            "margin": "1rem",})
                            ])
                        ], label="Выручка по врачу")
                    ]),
                ], style={'margin-left': '15rem',})
            ]),
        ])
    ], 
    )

#CALLBACK---------------------------------------- 

# Создаем обработчик события для обновления графиков в соответствии с выбранным месяцем

@app.callback(
    [Output('delta-indicator-1', 'figure'),
     Output('delta-indicator-2', 'figure'),
     Output('plan-label', 'children'),
     Output('plan-label2', 'children'),
     Output('specialization-sales', 'data'),
     Output('doctor-sales', 'data'),
     Output('runratewmt1-label', 'children'),
     Output('runratewmt2-label', 'children'),
     Output('plan-progress-wmt1-label', 'children'),
     Output('plan-progress-wmt2-label', 'children')],
    [Input('month_dropdown', 'value'),
     Input('departments_dropdown', 'value'),
     Input('filial_dropdown', 'value')]
)
def update_delta_indicators(selected_month, selected_department, selected_filial):
    # Фильтруем данные по выбранному месяцу
    current_month = selected_month
    
    data_specialization = sales_group(df, selected_month, selected_filial, selected_department, '','specname')
    data_doctor = sales_group(df, selected_month, selected_filial, selected_department, '', 'dname')
    
    # Индикаторы ВМТ 1
    fig2 = indicators(selected_month, 'ПЕРСОНА-МЕД', df, plan_df, selected_department)[0]
    
    # Индикаторы ВМТ 2
    fig3 = indicators(selected_month, 'ВМТ 2', df, plan_df, selected_department)[0]
    
    plan_label = html.Div([
        dbc.Alert([
            html.H4([f"План WMT 1 на {current_month}", 
                 dbc.Badge(f"{plan_filtred_month(current_month, 'ПЕРСОНА-МЕД', selected_department):,.0f} ₽",
                           color="info",  
                           className="ms-1")]), 
            ], color="warning"
                )
    ])

    plan_label2 = html.Div([
        dbc.Alert([
            html.H4([f"План WMT 2 на {current_month}", 
                 dbc.Badge(f"{plan_filtred_month(current_month, 'ВМТ 2', selected_department):,.0f} ₽",
                           color="info",  
                           className="ms-1")]), 
            ], color="warning"
                )
    ])
    
    run_rate_wmt1 = dbc.Alert([
        html.P(f"Прогноз выручки и выполнения плана на конец месяца", className="alert-heading",),
        dbc.Placeholder(size="xs", className="me-1 mt-1 w-100"),
        html.H5([f"{(indicators(current_month, 'ПЕРСОНА-МЕД', df, plan_df, selected_department)[1]):,.0f} ₽", 
                 dbc.Badge(f"{(indicators(current_month, 'ПЕРСОНА-МЕД', df, plan_df, selected_department)[2]):,.0f} %",
                           color="info",  
                           className="ms-1")]),
        ], color="light")
    
    run_rate_wmt2 = dbc.Alert([
    html.P(f"Прогноз выручки и выполнения плана на конец месяца", className="alert-heading",),
    dbc.Placeholder(size="xs", className="me-1 mt-1 w-100"),
    html.H5([f"{(indicators(current_month, 'ВМТ 2', df, plan_df, selected_department)[1]):,.0f} ₽", 
                dbc.Badge(f"{(indicators(current_month, 'ВМТ 2', df, plan_df, selected_department)[2]):,.0f} %",
                        color="info",  
                        className="ms-1")]),
    ], color="light")
    
    plan_progress_wmt1 = dbc.Alert([
    html.P(f"Текущий % выполнения плана", className="alert-heading",),
    dbc.Placeholder(size="xs", className="me-1 mt-1 w-100"),
    html.H1([dbc.Badge(f"{(indicators(current_month, 'ПЕРСОНА-МЕД', df, plan_df, selected_department)[3]):,.0f} %",
                        color="info",  
                        className="ms-5")]),
    ], color="light")

    plan_progress_wmt2 = dbc.Alert([
        html.P(f"Текущий % выполнения плана", className="alert-heading",),
        dbc.Placeholder(size="xs", className="me-1 mt-1 w-100"),
        html.H1([dbc.Badge(f"{(indicators(current_month, 'ВМТ 2', df, plan_df, selected_department)[3]):,.0f} %",
                            color="info",  
                            className="ms-5")]),
        ], color="light")

 
    return fig2, fig3, plan_label, plan_label2, data_specialization, data_doctor, run_rate_wmt1, run_rate_wmt2, plan_progress_wmt1, plan_progress_wmt2

@app.callback(
    [Output('graph-1', 'figure'),
     Output('graph-2', 'figure'),],
    [Input('month_dropdown', 'value'),
     Input('departments_dropdown', 'value'),
     Input('filial_dropdown', 'value')]
)
def update_dynamics(selected_month, selected_department, selected_filial):
    
    current_month = selected_month
    if selected_department:
        department_filter = selected_department
        filtered_df = df[(df['month_text'] == current_month) & (df['sname'] == department_filter)]
    else:
        filtered_df = df[df['month_text'] == current_month]
    
    fig1 = go.Figure()
    fig7 = None
    if not filtered_df.empty and selected_filial:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=gropped_filial_amount_period(filtered_df, selected_filial, '1D')[0],
            y=gropped_filial_amount_period(filtered_df, selected_filial, '1D')[1],
            name=selected_filial,
            marker_color='#63DFDC',
            text=gropped_filial_amount_period(filtered_df, selected_filial, '1D')[1].apply(lambda x: f'{x:,.0f}₽'),
        ))
        fig1.update_layout(
                    legend_orientation='h', # Устанавливасем горизонтальную ориентацию легенды
                    legend=dict(x=.2, xanchor="center"), # Меняем положение легенды на центрально
                    xaxis_title='Дата', # Устанавливаем название оси x
                    yaxis_title='Выручка, руб.', # Устанавливаем название оси y
                    hovermode='x',
                    margin=dict(l=5, r=5, t=5, b=5),  # Устанавливаем отступы
                    plot_bgcolor='white', # Устанавливаем белый цвет заднего фона
                        xaxis=dict(
                            showgrid=False,  # Отображаем сетку по оси X
                            gridcolor='#404040'),  # Устанавливаем цвет сетки по оси X
                        yaxis=dict(
                            showgrid=False,  # Отображаем сетку по оси Y
                            gridcolor='#404040'),  # Устанавливаем цвет сетки по оси Y
                    autosize=True,  # Отключаем автоматическое изменение размеров графика
                    )
        fig1.update_traces(hoverinfo='all', hovertemplate='Дата: %{x}<br>Выручка: %{y}')
    else:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=gropped_filial_amount_period(filtered_df, 'ПЕРСОНА-МЕД', '1D')[0],
            y=gropped_filial_amount_period(filtered_df, 'ПЕРСОНА-МЕД', '1D')[1],
            name='ПЕРСОНА-МЕД',
            marker_color='#63DFDC',
            text=gropped_filial_amount_period(filtered_df, 'ПЕРСОНА-МЕД', '1D')[1].apply(lambda x: f'{x:,.0f}₽'),
        ))
        fig1.add_trace(go.Bar(
            x=gropped_filial_amount_period(filtered_df, 'ВМТ 2', '1D')[0],
            y=gropped_filial_amount_period(filtered_df, 'ВМТ 2', '1D')[1],
            name='ВМТ 2',
            marker_color='#015965',
            text=gropped_filial_amount_period(filtered_df, 'ВМТ 2', '1D')[1].apply(lambda x: f'{x:,.0f}₽'),
            texttemplate='%{text}',
            textposition='auto'  # Позиция текста над столбиками 
        ))
        fig1.update_layout(
                        legend_orientation='h', # Устанавливасем горизонтальную ориентацию легенды
                        legend=dict(x=.2, xanchor="center"), # Меняем положение легенды на центрально
                        xaxis_title='Дата', # Устанавливаем название оси x
                        yaxis_title='Выручка, руб.', # Устанавливаем название оси y
                        hovermode='x',
                        margin=dict(l=5, r=5, t=5, b=5),  # Устанавливаем отступы
                        plot_bgcolor='white', # Устанавливаем белый цвет заднего фона
                            xaxis=dict(
                                showgrid=False,  # Отображаем сетку по оси X
                                gridcolor='#404040'),  # Устанавливаем цвет сетки по оси X
                            yaxis=dict(
                                showgrid=False,  # Отображаем сетку по оси Y
                                gridcolor='#404040'),  # Устанавливаем цвет сетки по оси Y
                        autosize=True,  # Отключаем автоматическое изменение размеров графика
                        )
        fig1.update_traces(hoverinfo='all', hovertemplate='Дата: %{x}<br>Выручка: %{y}')
        
    fig7 = dynamic_by_year(df, df_until, plan_df, selected_department)
        
    return fig1, fig7

if __name__ == "__main__":
    # app.run_server(debug=True, host='127.0.0.1')
    app.run_server(host="0.0.0.0", port="80")
