from cProfile import label
import datetime
from posixpath import defpath
#from turtle import color
import xdrlib
from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from os import path
import dash
from dash import dcc
from dash import html
import matplotlib
matplotlib.use('Agg')
from matplotlib.pyplot import legend, xlabel, ylabel
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from dash.dependencies import Input,Output
from sklearn.manifold import locally_linear_embedding

import forms
import detection_date
import clasificacion_texto

#from text_classif.classification.py import predict_activity

#from pymysql import NULL

app = Flask(__name__)
# Conexion a sql
app.config['MYSQL_HOST'] = '127.0.0.1'
#app.config['MYSQL_HOST'] = 'localhost'
#app.config['MYSQL_HOST'] = 'bdwumf34burl3arg3wug-mysql.services.clever-cloud.com'

app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_USER'] = 'u8wtjekkvx6ew9di'
app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_PASSWORD'] = 'dQVujvVE1krN6iBoLBDi'
# Nombre de la BD en phpmyadmin
app.config['MYSQL_DB'] = '2021213_DB_SINHERENCIA'
# app.config['MYSQL_DB'] = 'tdp_sw_s6'
# app.config['MYSQL_DB'] = 'bdwumf34burl3arg3wug'
# CURSOR
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# Configuracion
app.secret_key = '123456'

## Variables
current_date = datetime.datetime.now()
hora_citas = {
    -1 : '',
    7 : '7:00 - 8:00'  ,   
    8 : '8:00 - 9:00'  ,
    9 : '9:00 - 10:00' ,
    10: '10:00 - 11:00', 
    11: '11:00 - 12:00', 
    12: '12:00 - 13:00', 
    15: '15:00 - 16:00', 
    16: '16:00 - 17:00', 
    17: '17:00 - 18:00', 
    18: '18:00 - 19:00', 
    19: '19:00 - 20:00', 
    20: '20:00 - 21:00', 
    21: '21:00 - 22:00'
}
## Variables para buscar actividades
variables = ['Todos','Estrés','Depresión','Ansiedad']

## Variables para los test
respuestas_test = ['Nunca', 'A veces','Frecuentemente','Siempre']
preguntas_ansiedad = ['Me di cuenta que tenía la boca seca',
                      'Se me hizo difícil respirar',
                      'Sentí que mis manos temblaban',
                      'Estaba preocupado por situaciones en las cuales podía tener pánico o en las que podría hacer el ridículo',
                      'Sentí que estaba al punto de pánico',
                      'Sentí los latidos de mi corazón a pesar de no haber hecho ningún esfuerzo físico',
                      'Tuve miedo sin razón']

preguntas_depresion = ['No podía sentir ningún sentimiento positivo',
                       'Se me hizo difícil tomar la iniciativa para hacer cosas',
                       'He sentido que no había nada que me ilusionara',
                       'Me sentí triste y deprimido',
                       'No me pude entusiasmar por nada',
                       'Sentí que valía muy poco como persona',
                       'Sentí que la vida no tenía ningún sentido']

preguntas_estres = ['Me ha costado mucho descargar la tensión',
                    'Reaccioné exageradamente en ciertas situaciones',
                    'He sentido que estaba gastando una gran cantidad de energía',
                    'Me he sentido inquieto',
                    'Se me hizo difícil relajarme',
                    'No toleré nada que no me permitiera continuar con lo que estaba haciendo',
                    'He tendido a sentirme enfadado con facilidad']
## Nombre de Emoticones
img_emoticones = ['sin sintomas.png','leve.png','moderada.png','severa.png','extremadamente severa.png']

# HOME (Página de Inicio)
@app.route('/')
def home():
    return render_template('login.html')

# El usuario esta loggeado
def is_logged():
    if 'usuario' in session:
        return True
    return False

# Listar citas del psicologo
@app.route('/listar_citas', methods=['GET','POST'])
def listar_citas():
    error = None
    if is_logged():
        id_psicologo = session['usuario']['id_psicologo']
        
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT r.*, a.nombres, a.apellidos
            FROM `reserva_cita` r,
                 `alumno` a
            WHERE r.`id_alumno` = a.`id_alumno`
            AND r.`id_psicologo` = %s
            """,
            [id_psicologo]
        )
        lista_citas = cur.fetchall()

        ####################################
            
        if request.method == 'POST':
            
                id_data_alumno=request.form['id_data_alumno']
                print(id_data_alumno)
        
                cur.execute("""SELECT a.id_escala, a.Ddesarrollo, a.puntaje, a.id_alumno, a.nivel_variable, e.nom_variable AS Variable,
                EXTRACT(month FROM a.Ddesarrollo) AS Meses
                FROM alumno_escala AS a JOIN escala AS e ON a.id_escala = e.id_escala
                WHERE a.id_alumno = %s""", (id_data_alumno,))
                data_alumno = cur.fetchall()
                global lc_alumno  
                lc_alumno=pd.DataFrame(data_alumno, columns=['id_escala', 'Ddesarrollo', 'puntaje','id_alumno','nivel_variable', 'Variable', 'Meses'])

                return redirect(url_for('/datos_alumno/'))

        
        return render_template('listar_citas.html',
                                error=error,
                                lista_citas=lista_citas)
    else:
        return redirect(url_for('login'))

#Ver Datos Alumnos
dash_app4=dash.Dash(server=app,name="Datos Alumno", url_base_pathname="/datos_alumno/")
dash_app4.layout=html.Div(
               children=[
                   html.H1(children="Gráfico de barras"),
                   html.H3(children="Selecciona el nombre de la variable sobre la cual desea ves sus datos:"),
                   dcc.Dropdown(
                       id="tipo_escala_dropdown2",
                       options=[
                           {'label': 'General', 'value':0},
                           {'label': 'Ansiedad', 'value':1},
                           {'label': 'Depresión', 'value':2},
                           {'label': 'Estrés', 'value':3}
                       ],
                       value=0
                   ),
                   html.H3(children="Selecciona el mes que deseas visualizar:"),
                   dcc.Dropdown(
                       id="mes_dropdown2",
                       options=[
                            {'label': 'General', 'value':0},
                            {'label': 'Enero', 'value':1},
                            {'label': 'Febrero', 'value':2},
                            {'label': 'Marzo', 'value':3},
                            {'label': 'Abril', 'value':4},
                            {'label': 'Mayo', 'value':5},
                            {'label': 'Junio', 'value':6},
                            {'label': 'Julio', 'value':7},
                            {'label': 'Agosto', 'value':8},
                            {'label': 'Septiembre', 'value':9},
                            {'label': 'Octubre', 'value':10},
                            {'label': 'Noviembre', 'value':11},
                            {'label': 'Diciembre', 'value':12}
                       ],
                       value=0
                   ),
                   dcc.Graph(
                       id="graf-barra-alumno2",
                       figure={}              
                   ),
                   html.A(children="Volver", href="/listar_citas"),
               ], className="main-div"
           )
@dash_app4.callback(
    Output('graf-barra-alumno2', component_property='figure'),
    Input('tipo_escala_dropdown2', component_property='value'),
    Input('mes_dropdown2', component_property='value')
)
def update_graf_barra_alumno(value,value2):
    global lc_alumno
    if value==0:
        if value2==0:
            ndw=lc_alumno
            figure=px.bar(ndw, x="Variable", y="puntaje", color="nivel_variable", hover_data=['Ddesarrollo'], 
                labels={'nivel_variable':'Nivel de Variable', 'puntaje':'Puntaje Obtenido','Variable':'Variables','Ddesarrollo':'Fecha'})
        else:
            ndw=lc_alumno[lc_alumno['Meses']==value2]
            figure=px.bar(ndw, x="Variable", y="puntaje", color="nivel_variable", hover_data=['Ddesarrollo'], 
                labels={'nivel_variable':'Nivel de Variable', 'puntaje':'Puntaje Obtenido','Variable':'Variables','Ddesarrollo':'Fecha'})
    else:
        if value2==0:
            ndw=lc_alumno[lc_alumno['id_escala']==value]
            figure=px.bar(ndw, x="nivel_variable", y="puntaje", color="nivel_variable", hover_data=['Ddesarrollo'], 
                labels={'nivel_variable':'Nivel de Variable', 'puntaje':'Puntaje Obtenido','Ddesarrollo':'Fecha'})
        else:
            ndw=lc_alumno[lc_alumno['id_escala']==value]
            ndw=ndw[ndw['Meses']==value2]
            figure=px.bar(ndw, x="nivel_variable", y="puntaje", color="nivel_variable", hover_data=['Ddesarrollo'], 
                labels={'nivel_variable':'Nivel de Variable', 'puntaje':'Puntaje Obtenido','Ddesarrollo':'Fecha'})
    
    return figure

#####################################################################################################
# Eliminar actividad
@app.route('/eliminar_actividad', methods=['POST'])
def eliminar_actividad():
    error = None
    if is_logged():
        if request.method == 'POST':
            
            cur = mysql.connection.cursor()
            
            id_actividad = request.form['id_actividad']
            cur.execute("""
                    DELETE FROM actividades WHERE `actividades`.`id_actividad` = %s
                    """,
                    [id_actividad])
            
            mysql.connection.commit()
            cur.close()
            
            flash('Se elimino la actividad correctamente.')

        return redirect(url_for('registrar_actividad'))
    else:
        return redirect(url_for('login'))


# Registrar actividad
################################################
# Registrar actividades por parte del psicologo
@app.route('/registrar_actividad', methods=['GET', 'POST'])
def registrar_actividad():
    error = None
    if is_logged():
        id_psicologo = session['usuario']['id_psicologo']
        cur = mysql.connection.cursor()
        if request.method == 'POST':
            
            nom_actividad = request.form['nom_actividad']
            desc_actividad = request.form['desc_actividad']
            variable = clasificacion_texto.predict_activity(desc_actividad)[0]

            ###############################################################
            ## Fecha como input
            # fecha = request.form.get('fecha')
            # check_fecha = request.form.get('check_fecha')

            ###############################################################


            print(nom_actividad, desc_actividad)
            print('variable:',variable)

            ################################################################
            ## Deteccion de fechas
            arr_dates = detection_date.get_date_list(desc_actividad.lower())
            fecha = detection_date.get_date_by_points(arr_dates)
            print('posibles fechas\n', arr_dates)
            print(fecha)
            ################################################################

            cur.execute("""
                    INSERT INTO `actividades` 
                    (`nom_actividad`, `descripcion`, `id_psicologo`, `variable`, `fecha`) 
                    VALUES
                    (%s,%s,%s,%s, %s)
                    """,
                    [ nom_actividad, desc_actividad, id_psicologo, variable, fecha])
            mysql.connection.commit()
            flash('Se registro la actividad correctamente.')

        ## Listamos las actividades registradas por el psicologo.
        cur.execute(
            """
            SELECT *
            FROM `actividades`
            WHERE id_psicologo = %s
            """,
            [id_psicologo]
        )
        lista_actividades = cur.fetchall()
        cur.close()
        return render_template('registrar_actividad.html',
                                error=error,
                                lista_actividades=lista_actividades,
                                current_date=current_date)
    else:
        return redirect(url_for('login'))

# Registrar horario psicologo
@app.route('/registro_horario', methods=['GET', 'POST'])
def registrar_horario(error=None):
    # error = None
    if is_logged():
        id_psicologo = session['usuario']['id_psicologo']
        cur = mysql.connection.cursor()
        
        if request.method == 'POST':
            
            fecha = request.form['fecha']
            hora = int(request.form['hora'])
            
            if hora == -1 or not fecha:
                error="Debe ingresar todos los campos para registrar el horario."
            else:
                h_inicio = datetime.timedelta(hours=hora)
                h_fin = datetime.timedelta(hours=hora + 1)
                
                # Ya existe ese horario
                cur.execute("""
                    SELECT 1
                    FROM horario h
                    WHERE h.id_psicologo = %s
                    AND h.dia = %s
                    AND h.h_inicio = %s
                    """,
                    [id_psicologo, fecha, h_inicio]
                )
                validar = cur.fetchone()
                
                if validar is None:
                    cur.execute("""
                        INSERT INTO `horario` 
                        (`dia`, `h_inicio`, `h_fin`, `id_psicologo`, `estado`) 
                        VALUES
                        (%s,%s,%s,%s, %s)
                        """,
                        [ fecha, h_inicio, h_fin, id_psicologo, '0'])
                    mysql.connection.commit()
                    flash('Se registro el horario correctamente.')
                else:
                    error='Ya tiene un horario registrado en esa fecha y hora.'
        
        cur.execute(
            """
            SELECT p.nombres , h.* 
            FROM `horario` h,
                `psicologo` p
            WHERE h.id_psicologo = p.id_psicologo
            AND p.id_psicologo = %s
            """,
            [id_psicologo]
        )
        resultado_horario = cur.fetchall()
        cur.close()

        return render_template('registrar_horario.html', hora_citas=hora_citas,
                                                        resultado_horario=resultado_horario,
                                                        error=error,
                                                        current_date=current_date)
    else:
        return redirect(url_for('login'))

# Eliminar horario
@app.route('/eliminar_horario', methods=['POST'])
def eliminar_horario():
    error = None
    if is_logged():
        if request.method == 'POST':
            
            id_horario = request.form['id_horario']
            estado = request.form['estado']

            # borrar
            estado = '0'

            if estado == '1':
                error='No puede eliminar el horario de la cita cuando esta en estado RESERVADO.'
            else:
                cur = mysql.connection.cursor()
                cur.execute("""
                        DELETE FROM horario WHERE `horario`.`id_horario` = %s
                        """,
                        [id_horario])
                
                mysql.connection.commit()
                cur.close()
                
                flash('Se elimino el horario correctamente.')

        return redirect(url_for('registrar_horario', error=error))
    else:
        return redirect(url_for('login'))

# Registrar cita alumno
@app.route('/registro_cita', methods=['POST'])
def registrar_cita():
    if is_logged():
        id_alumno = session['usuario']['id_alumno']
        
        # obtenemos los datos del horario
        id_horario = request.form['id_horario']
        
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT p.id_psicologo , h.dia, h.h_inicio
            FROM `horario` h,
                `psicologo` p
            WHERE h.id_psicologo = p.id_psicologo
            AND h.id_horario = %s
        """, [id_horario])
        horario = cur.fetchone()

        if horario is not None:
            cur.execute(
                """INSERT INTO `reserva_cita` 
                (`dia`, `hora`, `id_psicologo`, `id_alumno`) 
                VALUES 
                (%s,%s,%s,%s)
                """,
                [ horario['dia'], horario['h_inicio'], horario['id_psicologo'], id_alumno ]
            )
            
            # Cambiamos el estado del horario
            cur.execute(
                """
                UPDATE `horario`
                SET `estado` = '1'
                WHERE `horario`.`id_horario` = %s
                """,
                [id_horario]
            )
            mysql.connection.commit()
            cur.close()

            flash('Se registro la cita correctamente')
        else:
            flash('No existe el horario seleccionado')
        
        cur.close()
        return redirect(url_for('buscar_cita'))
    else:
        return redirect(url_for('login'))

# Buscar y Listar cita
@app.route('/buscar_cita', methods=['GET','POST'])
def buscar_cita():
    error=None
    if is_logged():
        resultado_cita = []

        if request.method == 'POST':
            fecha = request.form['fecha']
            hora = int(request.form['hora'])

            if hora == -1 or not fecha:
                error="Complete los campos fecha y hora para aplicar el filtro, por favor."
            else:
                h_inicio = datetime.timedelta(hours=hora)
                h_fin = datetime.timedelta(hours=hora + 1)

                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT p.nombres , h.* 
                    FROM `horario` h,
                        `psicologo` p
                    WHERE h.id_psicologo = p.id_psicologo
                    AND h.estado = 0
                    AND h.DIA = %s
                    AND h.h_inicio = %s
                    AND h.h_fin = %s
                """, 
                [fecha, h_inicio, h_fin])
                resultado_cita = cur.fetchall()
                cur.close()
                return render_template('buscar_cita.html', 
                                hora_citas=hora_citas, 
                                resultado_cita=resultado_cita,
                                error=error,
                                fecha=fecha,
                                hora=hora)

        
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT p.nombres , h.* 
            FROM `horario` h,
                `psicologo` p
            WHERE h.id_psicologo = p.id_psicologo
            AND h.estado = 0
        """)
        resultado_cita = cur.fetchall()
        cur.close()

        return render_template('buscar_cita.html', 
                                hora_citas=hora_citas, 
                                resultado_cita=resultado_cita,
                                error=error)
    else:
        print('no usuario')
        return redirect(url_for('login'))

# Buscar actividades
@app.route('/buscar_actividad', methods=['GET','POST'])
def buscar_actividad():
    if is_logged():
        actividades = []
        if request.method == 'POST':
            variable = request.form['variable']

            cur = mysql.connection.cursor()

            cur.execute("""
                SELECT * 
                FROM `actividades` a
                WHERE (a.`variable` = %s OR 'Todos' = %s)
                AND (`a`.`fecha` >= CURRENT_DATE
                     OR `a`.`fecha` IS NULL)
                ORDER BY ISNULL(`a`.`fecha`), `a`.`fecha`
            """, 
            [variable, variable])
            actividades = cur.fetchall()

            cur.close()

        else:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT *
                FROM `actividades` a
                WHERE (`a`.`fecha` >= CURRENT_DATE
                     OR `a`.`fecha` IS NULL)
                ORDER BY ISNULL(`a`.`fecha`), `a`.`fecha`
            """)
            actividades = cur.fetchall()
            cur.close()
        return render_template('buscar_actividad.html', variables=variables,
                                                        actividades=actividades)
    else:
        return redirect(url_for('login'))

# Detalle actvidad
@app.route('/detalle_actividad', methods=['POST'])
def detalle_actividad():
    error = None
    if is_logged():
        actividad = None
        if request.method == 'POST':
            id_actividad = request.form.get('id_actividad')
            print('llego a detalle actividad', id_actividad)
            
            # Obtenemos la actividad
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT *
                FROM actividades a
                WHERE a.id_actividad = %s
            """,
            [id_actividad]
            )
            actividad = cur.fetchone()
            cur.close()

        return render_template('detalle_actividad.html',
                                actividad=actividad)
    else:
        return redirect(url_for('login'))

# Visualizar resultados de test y recomendacion de actividades
@app.route('/visualizar_resultado/<id_alumno_escala>', methods=['GET'])
def visualizar_resultado(id_alumno_escala):
    if is_logged():
        print('id_alumno_escala:', id_alumno_escala)
        actividades = None
        name_emoticon = None
        cur = mysql.connection.cursor()

        # Obtenemos el resultado del alumno de la tabla alumno escala
        cur.execute("""
            SELECT ae.`puntaje`, 
                    e.`id_escala`, 
                    e.`nom_variable`,
                    ae.`nivel_variable`
            FROM `alumno_escala` ae,
                 `escala` e
            WHERE e.`id_escala` = ae.`id_escala`
            AND ae.`id_alumno_escala` = %s
        """,
        [id_alumno_escala])
        resultado_test = cur.fetchone()

        puntaje = resultado_test['puntaje']
        id_escala = resultado_test['id_escala']
        nom_variable = resultado_test['nom_variable']


        if (id_escala == 1 and puntaje >=4) or \
            (id_escala == 2 and puntaje >=5) or \
            (id_escala == 3 and puntaje >=8):
            cur.execute("""
                SELECT * 
                FROM `actividades` a
                WHERE a.`variable` = %s
                AND (`a`.`fecha` >= CURRENT_DATE
                     OR `a`.`fecha` IS NULL)
                ORDER BY ISNULL(`a`.`fecha`), `a`.`fecha`
            """, 
            [nom_variable])
            actividades = cur.fetchall()

        cur.close()

        ## Logica para la imagen
        if id_escala == 1: ## ansiedad
            if puntaje<4: 
                name_emoticon=img_emoticones[0]
            elif puntaje==4:
                name_emoticon=img_emoticones[1]
            elif puntaje>=5 and puntaje<=7:
                name_emoticon=img_emoticones[2]
            elif puntaje==8 or puntaje == 9:
                name_emoticon=img_emoticones[3]
            else:
                name_emoticon=img_emoticones[4]
        elif id_escala == 2: ## depresion
            if puntaje<=4:
                name_emoticon=img_emoticones[0]
            elif puntaje==5 or puntaje == 6:
                name_emoticon=img_emoticones[1]
            elif puntaje>=7 and puntaje<=10:
                name_emoticon=img_emoticones[2]
            elif puntaje>=11 and puntaje <= 13:
                name_emoticon=img_emoticones[3]
            else:
                name_emoticon=img_emoticones[4]
        else: ## id_escala == 3 - estres
            if puntaje<=7:
                name_emoticon=img_emoticones[0]
            elif puntaje==8 or puntaje == 9:
                name_emoticon=img_emoticones[1]
            elif puntaje>=10 and puntaje<=12:
                name_emoticon=img_emoticones[2]
            elif puntaje>=13 and puntaje <= 16:
                name_emoticon=img_emoticones[3]
            else:
                name_emoticon=img_emoticones[4]

        url_emoticon = url_for('static', filename='imagenes/' + name_emoticon)
        return render_template('resultado_test.html',
                                actividades=actividades,
                                resultado_test=resultado_test,
                                url_emoticon=url_emoticon)
    else:
        return redirect(url_for('login'))


# Test Psicologico
@app.route('/test_psicologico_main', methods=['GET','POST'])
def test_psicologico_main():
    if is_logged():
        return render_template('test_psicologico_main.html')
    else:
        print('no usuario')
        return redirect(url_for('login'))

# Test de Ansiedad
@app.route('/test_ansiedad', methods=['GET','POST'])
def test_ansiedad():
    if is_logged():
        error = None
        if request.method == 'POST':

            id_alumno= session['usuario']['id_alumno']

            if request.form.get('1') is None or \
               request.form.get('2') is None or \
               request.form.get('3') is None or \
               request.form.get('4') is None or \
               request.form.get('5') is None or \
               request.form.get('6') is None or \
               request.form.get('7') is None:
                error = 'Completa todos los campos necesarios, por favor'
            else:

                p1 = int(request.form.get('1'))
                p2 = int(request.form.get('2'))
                p3 = int(request.form.get('3'))
                p4 = int(request.form.get('4'))
                p5 = int(request.form.get('5'))
                p6 = int(request.form.get('6'))
                p7 = int(request.form.get('7'))

                puntaje_total=p1+p2+p3+p4+p5+p6+p7
                puntaje_total=int(puntaje_total)
                nivel_variable="Temp"
                desarrollo=datetime.datetime.now()
                desarrollo=desarrollo.strftime('%Y-%m-%d')

                if puntaje_total==4:
                    nivel_variable="Ansiedad Leve"
                elif puntaje_total>=5 and puntaje_total<=7:
                    nivel_variable="Ansiedad Moderada"
                elif puntaje_total==8 or puntaje_total == 9:
                    nivel_variable="Ansiedad Severa"
                elif puntaje_total<4:
                    nivel_variable="Sin Ansiedad"
                else:
                    nivel_variable="Ansiedad Extremadamente Severa"

                cur = mysql.connection.cursor()

                cur.execute(
                    "INSERT INTO alumno_escala (id_escala, Ddesarrollo, puntaje, nivel_variable, id_alumno) VALUES (%s,%s,%s,%s,%s)",
                    (1, desarrollo, puntaje_total, nivel_variable, id_alumno))
                mysql.connection.commit()

                ruta = url_for('visualizar_resultado', id_alumno_escala=cur.lastrowid)

                print("Se registró la escala correctamente.")
                cur.close()
                return redirect(ruta)
        return render_template('test_ansiedad.html',
                                preguntas=preguntas_ansiedad,
                                respuestas_test=respuestas_test,
                                error=error)
    else:
        print('No usuario')
        return redirect(url_for('login'))
# Test de Depresión
@app.route('/test_depresion', methods=['GET','POST'])
def test_depresion():
    if is_logged():
        error = None
        if request.method == 'POST':

            id_alumno= session['usuario']['id_alumno']
            
            if request.form.get('1') is None or \
               request.form.get('2') is None or \
               request.form.get('3') is None or \
               request.form.get('4') is None or \
               request.form.get('5') is None or \
               request.form.get('6') is None or \
               request.form.get('7') is None:
                error = 'Completa todos los campos necesarios, por favor'
            else:

                p1 = int(request.form.get('1'))
                p2 = int(request.form.get('2'))
                p3 = int(request.form.get('3'))
                p4 = int(request.form.get('4'))
                p5 = int(request.form.get('5'))
                p6 = int(request.form.get('6'))
                p7 = int(request.form.get('7'))


                puntaje_total=p1+p2+p3+p4+p5+p6+p7
                puntaje_total=int(puntaje_total)
                nivel_variable="Temp"
                desarrollo=datetime.datetime.now()
                desarrollo=desarrollo.strftime('%Y-%m-%d')

                if puntaje_total==5 or puntaje_total == 6:
                    nivel_variable="Depresión Leve"
                elif puntaje_total>=7 and puntaje_total<=10:
                    nivel_variable="Depresión Moderada"
                elif puntaje_total>=11 and puntaje_total <= 13:
                    nivel_variable="Depresión Severa"
                elif puntaje_total<=4:
                    nivel_variable="Sin Depresión"
                else:
                    nivel_variable="Depresión Extremadamente Severa"

                cur = mysql.connection.cursor()

                cur.execute(
                    "INSERT INTO alumno_escala (id_escala, Ddesarrollo, puntaje, nivel_variable, id_alumno) VALUES (%s,%s,%s,%s,%s)",
                    (2, desarrollo, puntaje_total, nivel_variable, id_alumno))
                mysql.connection.commit()
                
                ruta = url_for('visualizar_resultado', id_alumno_escala=cur.lastrowid)

                print("Se registró la escala correctamente.")
                cur.close()
                return redirect(ruta)

        return render_template('test_depresion.html',
                                preguntas=preguntas_depresion,
                                respuestas_test=respuestas_test,
                                error=error)
    else:
        print('No usuario')
        return redirect(url_for('login'))

# Test de Estrés
@app.route('/test_estres', methods=['GET','POST'])
def test_estres():
    if is_logged():
        error = None
        if request.method == 'POST':

            id_alumno= session['usuario']['id_alumno']
            
            if request.form.get('1') is None or \
               request.form.get('2') is None or \
               request.form.get('3') is None or \
               request.form.get('4') is None or \
               request.form.get('5') is None or \
               request.form.get('6') is None or \
               request.form.get('7') is None:
                error = 'Completa todos los campos necesarios, por favor'
            else:

                p1 = int(request.form.get('1'))
                p2 = int(request.form.get('2'))
                p3 = int(request.form.get('3'))
                p4 = int(request.form.get('4'))
                p5 = int(request.form.get('5'))
                p6 = int(request.form.get('6'))
                p7 = int(request.form.get('7'))

                puntaje_total=p1+p2+p3+p4+p5+p6+p7
                puntaje_total=int(puntaje_total)
                nivel_variable="Temp"
                desarrollo=datetime.datetime.now()
                desarrollo=desarrollo.strftime("%Y-%m-%d")

                if puntaje_total==8 or puntaje_total == 9:
                    nivel_variable="Estrés Leve"
                elif puntaje_total>=10 and puntaje_total<=12:
                    nivel_variable="Estrés Moderado"
                elif puntaje_total>=13 and puntaje_total <= 16:
                    nivel_variable="Estrés Severo"
                elif puntaje_total<=7:
                    nivel_variable="Sin estrés"
                else:
                    nivel_variable="Estrés Extremadamente Severo"

                cur = mysql.connection.cursor()

                cur.execute(
                    "INSERT INTO alumno_escala (id_escala, Ddesarrollo, puntaje, nivel_variable, id_alumno) VALUES (%s,%s,%s,%s,%s)",
                    (3, desarrollo, puntaje_total, nivel_variable, id_alumno))
                mysql.connection.commit()

                ruta = url_for('visualizar_resultado', id_alumno_escala=cur.lastrowid)

                print("Se registró la escala correctamente.")
                cur.close()
                return redirect(ruta)
        
        return render_template('test_estres.html',
                                preguntas=preguntas_estres,
                                respuestas_test=respuestas_test,
                                error=error)
    else:
        print('No usuario')
        return redirect(url_for('login'))


# Registro Alumno:
@app.route('/registro_alumno', methods=['GET','POST'])
def registro_alumno():
    
    form = forms.AlumnoRegForm(request.form)
    if request.method == 'POST' and form.validate():
        
        # tabla persona
        nombres = form.nombres.data
        apellidos = form.apellidos.data
        email = form.email.data
        sede = form.sede.data
        contrasena = form.contrasena.data
        # tabla alumno
        carrera = form.carrera.data
        sexo = form.sexo.data
        ciclo = form.ciclo.data
        edad = form.edad.data

        #Para BD sin herencia
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO alumno (carrera, edad, ciclo, nombres, apellidos, email, contrasena, sexo, sede) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (carrera, edad, ciclo, nombres, apellidos, email, contrasena, sexo, sede))
        mysql.connection.commit()
        cur.close()

        flash('Usuario creado correctamente. Ingrese con su email y contraseña.')
        return redirect(url_for('login'))
    
    return render_template('registro_alumno.html', form=form)

# Editar Perfil Alumno
@app.route('/editar_perfil_a', methods=['GET','POST'])
def editar_perfil_a():
    if is_logged():

        # ID del alumno
        id_alumno= session['usuario']['id_alumno']
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT * 
            FROM `alumno`
            WHERE id_alumno = %s
            """,
            [id_alumno])
        alumno = cur.fetchone()

        if request.method == 'POST':

            # tabla persona
            nombres = alumno['nombres'] if not request.form['nombres'] else request.form['nombres']
            apellidos = alumno['apellidos'] if not request.form['apellidos'] else request.form['apellidos']
            email = alumno['email'] if not request.form['email'] else request.form['email']
            sede = alumno['sede'] if not request.form['sede'] else request.form['sede']
            contrasena = alumno['contrasena']
            # tabla alumno
            carrera = alumno['carrera'] if not request.form['carrera'] else request.form['carrera']
            sexo = alumno['sexo'] if not request.form['sexo'] else request.form['sexo']
            ciclo = alumno['ciclo'] if not request.form['ciclo'] else request.form['ciclo']
            edad = alumno['edad'] if not request.form['edad'] else request.form['edad']

            #Para BD sin herencia
            # cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE alumno set carrera=%s, edad=%s, ciclo=%s, nombres=%s, apellidos=%s, email=%s, contrasena=%s, sexo=%s, sede=%s WHERE id_alumno=%s",
                (carrera, edad, ciclo, nombres, apellidos, email, contrasena, sexo, sede, id_alumno))
            mysql.connection.commit()
            flash('Cambios guardados correctamente.')

            cur.execute(
                """
                SELECT * 
                FROM `alumno`
                WHERE id_alumno = %s
                """,
                [id_alumno])
            alumno = cur.fetchone()

        cur.close()
        return render_template('editar_perfil_a.html', alumno=alumno)
    else:
        print("No usuario")
        return redirect(url_for('login'))

################################################################################################################################################
#Estado Mental
@app.route('/estado_mental/', methods=['GET','POST'])
def estado_mental():
    if is_logged():
        cur = mysql.connection.cursor()
        id_alumno = session['usuario']['id_alumno']

        #cur.execute("SELECT * FROM alumno_escala WHERE id_alumno = %s", (id_alumno,))
        cur.execute("""SELECT a.id_escala, a.Ddesarrollo, a.puntaje, a.id_alumno, a.nivel_variable, e.nom_variable AS Variable,
         EXTRACT(month FROM a.Ddesarrollo) AS Meses
         FROM alumno_escala AS a JOIN escala AS e ON a.id_escala = e.id_escala
         WHERE a.id_alumno = %s""", (id_alumno,))
        alumno = cur.fetchall()

        global df
        #df=pd.DataFrame(alumno, columns=['id_alumno_escala','id_escala', 'Ddesarrollo', 'puntaje','nivel_variable','id_alumno'])       
        df=pd.DataFrame(alumno, columns=['id_escala', 'Ddesarrollo', 'puntaje','id_alumno','nivel_variable', 'Variable', 'Meses'])

        return render_template('estado_mental.html')
    else:
        return redirect(url_for('login'))

#DASHBOARD PSICOLOGO
#PIE
dash_app=dash.Dash(server=app,name="Dashboard", url_base_pathname="/graf_psi_pie/")
dash_app.layout=html.Div(
               children=[
                   html.H1(children="Gráfico Circular o Pie"),
                   html.H3(children="Selecciona el nombre de la variable sobre la cual desea ves sus datos:"),
                   dcc.Dropdown(
                       id="pie_escala_dropdown",
                       options=[
                           {'label': 'General', 'value':0},
                           {'label': 'Ansiedad', 'value':1},
                           {'label': 'Depresión', 'value':2},
                           {'label': 'Estrés', 'value':3}
                       ],
                       value=0
                   ),
                   html.H3('Seleccione el mes:'),
                   dcc.Dropdown(
                    id="pie_dropdown",
                    options=[
                        {'label': 'General', 'value':0},
                        {'label': 'Enero', 'value':1},
                        {'label': 'Febrero', 'value':2},
                        {'label': 'Marzo', 'value':3},
                        {'label': 'Abril', 'value':4},
                        {'label': 'Mayo', 'value':5},
                        {'label': 'Junio', 'value':6},
                        {'label': 'Julio', 'value':7},
                        {'label': 'Agosto', 'value':8},
                        {'label': 'Septiembre', 'value':9},
                        {'label': 'Octubre', 'value':10},
                        {'label': 'Noviembre', 'value':11},
                        {'label': 'Diciembre', 'value':12}
                    ],
                    value=0
                   ),
                   dcc.Graph(
                       id="graf-pie",
                       figure={}             
                   ),
                   html.A(children="Volver", href="/sesion_psicologo"),
               ], className="main-div"
           )
@dash_app.callback(
    Output('graf-pie', component_property='figure'),
    Input('pie_escala_dropdown', component_property='value'),
    Input('pie_dropdown', component_property='value')
    
)
def update_graf_pie(value,value2):
    global dfp3
    if value==0:
        if value2==0:
            df_meses=dfp3
            figure=px.pie(df_meses, names="Variable", values="Total", labels={'id_escala':'Variables'})
        else:
            df_meses=dfp3[dfp3['Meses']==value2]
            figure=px.pie(df_meses, names="Variable", values="Total", labels={'id_escala':'Variables'})

    else:
        if value2==0:
            df_meses=dfp3[dfp3['id_escala']==value]
            figure=px.pie(df_meses, names="nivel_variable", values="Total", labels={'id_escala':'Variables'})
        else:
            df_meses=dfp3[dfp3['id_escala']==value]
            df_meses=df_meses[df_meses['Meses']==value2]
            figure=px.pie(df_meses, names="nivel_variable", values="Total",labels={'id_escala':'Variables'})
    
    return figure
    

#LINE GRAPH

dash_app3=dash.Dash(server=app,name="Dashboard", url_base_pathname="/graf_psi_line/")
dash_app3.layout=html.Div(
            children=[
                html.H1(children="Gráfico de Línea"),
                html.H3('Seleccione el nombre de variable:'),
                dcc.Dropdown(
                    id="line_dropdown",
                       options=[
                           {'label': 'Ansiedad', 'value':1},
                           {'label': 'Depresión', 'value':2},
                           {'label': 'Estrés', 'value':3}
                       ],
                       value=1
                   ),
                html.H3('Seleccione la carrera'),
                dcc.Dropdown(
                    id="line_filter",
                    options=[

                           {'label': 'Ingenieria de sistemas de informacion', 'value':'Ingenieria de sistemas de informacion'},
                           {'label': 'Ingenieria de software', 'value':'Ingenieria de software'}
                       ],
                       value='Ingenieria de sistemas de informacion'
                   ),
                html.H3('Seleccione el sexo:'),
                dcc.Dropdown(
                    id="checklist",
                       options=[

                           {'label': 'Masculino', 'value':'Masculino'},
                           {'label': 'Femenino', 'value':'Femenino'}
                       ],
                       value='Masculino'
                   ),
                html.H3('Seleccione la sede:'),
                dcc.Dropdown(
                    id="checklist_2",
                       options=[
                           {'label': 'Monterrico', 'value':'Monterrico'},
                           {'label': 'San Isidro', 'value':'San Isidro'},
                           {'label': 'San Miguel', 'value':'San Miguel'},
                           {'label': 'Villa', 'value':'Villa'}
                       ],
                       value='Monterrico'
                   ),
                html.Hr(),
                dcc.Graph(
                    id="graf-line2",
                    figure={}
                                 
                ),
                html.A(children="Volver", href="/sesion_psicologo"),
            ], className="main-div"
        )
@dash_app3.callback(
    Output('graf-line2', component_property='figure'),
    Input('line_dropdown', component_property='value'),
    Input('line_filter', component_property='value'),
    Input('checklist', component_property='value'),
    Input('checklist_2', component_property='value')
)
def update_graf_line(value,filter,sex,sed):
    global asd
    print(value, filter, sex, sed)

    newColumn=pd.DataFrame(columns=['mes_n'])
    months=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

    for i in range (len(asd)):
        for j in range(len(months)):
            if asd['Mes'][i] == j+1:
                newColumn.loc[i] =months[j]

    asd["Mes_N"]=newColumn['mes_n']

    tempo=asd

    tempo=tempo[tempo['id_escala']==value]
    tempo=tempo[tempo['Carrera']==filter]
    tempo=tempo[tempo['Sexo']==sex]
    tempo=tempo[tempo['Sede']==sed]
    tempo.sort_values(by=['Mes'], inplace=True, ascending=True)
    tempo2=tempo.groupby(["Mes","Mes_N","nivel_variable"])["Mes"].count().reset_index(name="Total")
    print(tempo2)

    figure2=px.line(tempo2, x="Mes_N", y="Total", labels={'nivel_variable':'Nivel de Variable'}, color='nivel_variable', markers=True)

    print(tempo)
    
    return figure2


#######################################################################
#DASHBOARD ALUMNO
dash_app2=dash.Dash(server=app,name="Dashboard", url_base_pathname="/graf_barra_alumno/")
dash_app2.layout=html.Div(
               children=[
                   html.H1(children="Gráfico de barras"),
                   html.H3(children="Selecciona el nombre de la variable sobre la cual desea ves sus datos:"),
                   dcc.Dropdown(
                       id="tipo_escala_dropdown",
                       options=[
                           {'label': 'General', 'value':0},
                           {'label': 'Ansiedad', 'value':1},
                           {'label': 'Depresión', 'value':2},
                           {'label': 'Estrés', 'value':3}
                       ],
                       value=0
                   ),
                   html.H3(children="Selecciona el mes que deseas visualizar:"),
                   dcc.Dropdown(
                       id="mes_dropdown",
                       options=[
                            {'label': 'General', 'value':0},
                            {'label': 'Enero', 'value':1},
                            {'label': 'Febrero', 'value':2},
                            {'label': 'Marzo', 'value':3},
                            {'label': 'Abril', 'value':4},
                            {'label': 'Mayo', 'value':5},
                            {'label': 'Junio', 'value':6},
                            {'label': 'Julio', 'value':7},
                            {'label': 'Agosto', 'value':8},
                            {'label': 'Septiembre', 'value':9},
                            {'label': 'Octubre', 'value':10},
                            {'label': 'Noviembre', 'value':11},
                            {'label': 'Diciembre', 'value':12}
                       ],
                       value=0
                   ),
                   dcc.Graph(
                       id="graf-barra-alumno",
                       figure={}              
                   ),
                   html.A(children="Volver", href="/estado_mental/"),
               ], className="main-div"
           )
@dash_app2.callback(
    Output('graf-barra-alumno', component_property='figure'),
    Input('tipo_escala_dropdown', component_property='value'),
    Input('mes_dropdown', component_property='value')
)
def update_graf_barra_alumno(value,value2):
    global df
    if value==0:
        if value2==0:
            ndw=df
            figure=px.bar(ndw, x="Variable", y="puntaje", color="nivel_variable", hover_data=['Ddesarrollo'], 
                labels={'nivel_variable':'Nivel de Variable', 'puntaje':'Puntaje Obtenido','Variable':'Variables','Ddesarrollo':'Fecha'})
        else:
            ndw=df[df['Meses']==value2]
            figure=px.bar(ndw, x="Variable", y="puntaje", color="nivel_variable", hover_data=['Ddesarrollo'], 
                labels={'nivel_variable':'Nivel de Variable', 'puntaje':'Puntaje Obtenido','Variable':'Variables','Ddesarrollo':'Fecha'})
    else:
        if value2==0:
            ndw=df[df['id_escala']==value]
            figure=px.bar(ndw, x="nivel_variable", y="puntaje", color="nivel_variable", hover_data=['Ddesarrollo'], 
                labels={'nivel_variable':'Nivel de Variable', 'puntaje':'Puntaje Obtenido','Ddesarrollo':'Fecha'})
        else:
            ndw=df[df['id_escala']==value]
            ndw=ndw[ndw['Meses']==value2]
            figure=px.bar(ndw, x="nivel_variable", y="puntaje", color="nivel_variable", hover_data=['Ddesarrollo'], 
                labels={'nivel_variable':'Nivel de Variable', 'puntaje':'Puntaje Obtenido','Ddesarrollo':'Fecha'})
    
    return figure

################################################################################################################################################
# registro psicologo:
@app.route('/registro_psi', methods=['GET','POST'])
def registro_psi():

    form = forms.PsicoRegForm(request.form)
    if request.method == 'POST' and form.validate():

        # tabla persona
        nombres = form.nombres.data
        apellidos = form.apellidos.data
        email = form.email.data
        sede = form.sede.data
        contrasena = form.contrasena.data
        # tabla psicologo
        num_colegiado = form.num_colegiado.data

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO `psicologo` 
            (`num_colegiado`, `nombres`, `apellidos`, `email`, `contrasena`, `sede`) 
            VALUES
            (%s,%s,%s,%s,%s,%s)
        """,
            [num_colegiado, nombres, apellidos, email, contrasena, sede])

        mysql.connection.commit()
        cur.close()
        
        flash('Usuario creado correctamente. Ingrese con su email y contraseña.')
        return redirect(url_for('login'))
    
    return render_template('registro_psi.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        contrasena = request.form['contrasena']

        if not email or not contrasena:
            error = "Complete los campos necesarios por favor."
        else:    
            cur = mysql.connection.cursor()

            # Alumno
            cur.execute("SELECT * FROM alumno WHERE email= %s", (email,))
            alumno = cur.fetchone()
            
            # Psicologo
            cur.execute("SELECT * FROM psicologo WHERE email= %s", (email,))
            psicologo = cur.fetchone()
            
            cur.close()

            #Datos de Saludo

            if alumno is not None and contrasena == alumno["contrasena"]:
                session["usuario"] = alumno
                session["nombre"] = alumno['nombres']
                session["apellido"] = alumno['apellidos']
                session["carrera"] = alumno['carrera']
                session["edad"] = alumno['edad']
                session["ciclo"] = alumno['ciclo']
                session["email"] = alumno['email']
                session["contrasena"] = alumno['contrasena']
                session["sexo"] = alumno['sexo']
                session["sede"] = alumno['sede']
                return redirect(url_for('estado_mental'))

            elif psicologo is not None and contrasena == psicologo["contrasena"]:
                session["usuario"] = psicologo
                session["nombre"] = psicologo['nombres']
                session["apellido"] =psicologo['apellidos']
                return redirect(url_for('sesion_psicologo'))
            else:
                error="usuario o contraseña incorrectos. Intentelo de nuevo."

    return render_template('login.html', error=error)


@app.route('/sesion_psicologo')
def sesion_psicologo():
    if is_logged():
        cur = mysql.connection.cursor()

        #Line Graph
        cur.execute("""
        SELECT a.id_escala, a.Ddesarrollo, a.puntaje, a.id_alumno, a.nivel_variable, e.nom_variable as Variable, 
        EXTRACT(month FROM a.Ddesarrollo) AS Mes,o.sexo as Sexo,o.sede as Sede,o.carrera as Carrera
        FROM alumno_escala AS a
        JOIN escala AS e 
            ON a.id_escala = e.id_escala 
        JOIN alumno AS o
            ON o.id_alumno = a.id_alumno

        """)
        dsa = cur.fetchall()

        global asd
        asd=pd.DataFrame(dsa, columns=['id_escala', 'Ddesarrollo', 'puntaje','id_alumno','nivel_variable', 'Variable','Mes','Sexo','Sede','Carrera'])

        #DATOS PIE CHART
        cur.execute("""SELECT a.id_escala, a.Ddesarrollo, a.puntaje, a.id_alumno, a.nivel_variable, e.nom_variable AS Variable,
         EXTRACT(month FROM a.Ddesarrollo) AS Meses, 
         COUNT(a.nivel_variable) AS Total 
         FROM alumno_escala AS a JOIN escala AS e ON a.id_escala = e.id_escala
         GROUP BY a.nivel_variable, Meses""")
        datos_totales=cur.fetchall()
        global dfp3
        dfp3=pd.DataFrame(datos_totales, columns=['id_escala', 'Ddesarrollo', 'puntaje','id_alumno','nivel_variable', 'Variable', 'Meses', 'Total'])

        return render_template('sesion_psicologo.html')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port=3000, debug=True)
