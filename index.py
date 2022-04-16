import datetime
from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from os import path
import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd

#from text_classif.classification.py import predict_activity

#from pymysql import NULL

app = Flask(__name__)
# Conexion a sql
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
# Nombre de la BD en phpmyadmin
app.config['MYSQL_DB'] = '2021213_DB_SINHERENCIA'
# CURSOR
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# Configuracion
app.secret_key = '123456'

## Variables
current_date = datetime.datetime.now()
hora_citas = [
    ('7:00 - 8:00', 7),
    ('8:00 - 9:00', 8),
    ('9:00 - 10:00', 9),
    ('10:00 - 11:00', 10),
    ('11:00 - 12:00', 11),
    ('12:00 - 13:00', 12),
    ('15:00 - 16:00', 15),
    ('16:00 - 17:00', 16),
    ('17:00 - 18:00', 17),
    ('18:00 - 19:00', 18),
    ('19:00 - 20:00', 19),
    ('20:00 - 21:00', 20),
    ('21:00 - 22:00', 21)
]
## Variables para buscar actividades
variables = ['Todos','Estrés','Depresión','Ansiedad']

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
@app.route('/listar_citas', methods=['GET'])
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
        cur.close()
        return render_template('listar_citas.html',
                                error=error,
                                lista_citas=lista_citas)
    else:
        return redirect(url_for('login'))



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
## ESTO ES TEMPORAL
## TODO: MOVER A UN ARCHIVO A PARTE
import joblib

tr = joblib.load('text_classif/tfidf.pkl')
clf = joblib.load('text_classif/SVM.pkl')

def predict_activity(activity_text):
    value = tr.transform([activity_text])
    return clf.predict(value)

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
            variable = predict_activity(desc_actividad)[0]

            fecha = request.form.get('fecha')
            check_fecha = request.form.get('check_fecha')


            print(nom_actividad, desc_actividad)
            print('variable:',variable)
            print('fecha', fecha)
            print('check_fecha', check_fecha)
            
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
def registrar_horario():
    error = None
    if is_logged():
        id_psicologo = session['usuario']['id_psicologo']
        cur = mysql.connection.cursor()
        
        if request.method == 'POST':
            
            fecha = request.form['fecha']
            hora = int(request.form['hora'])

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
    if is_logged():
        resultado_cita = []
        if request.method == 'POST':
            fecha = request.form['fecha']
            hora = int(request.form['hora'])
            
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

        else:
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
                                resultado_cita=resultado_cita)
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
            """, 
            [variable, variable])
            actividades = cur.fetchall()

            cur.close()

        else:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT * 
                FROM `actividades`
            """)
            actividades = cur.fetchall()
            cur.close()
        return render_template('buscar_actividad.html', variables=variables,
                                                        actividades=actividades)
    else:
        return redirect(url_for('login'))


# Visualizar resultados de test y recomendacion de actividades
@app.route('/visualizar_resultado/<id_alumno_escala>', methods=['GET'])
def visualizar_resultado(id_alumno_escala):
    if is_logged():
        print('id_alumno_escala:', id_alumno_escala)
        actividades = None
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

        print(puntaje, type(puntaje))
        print(id_escala, type(id_escala))
        print(nom_variable, type(nom_variable))

        if (id_escala == 1 and puntaje >=4) or \
            (id_escala == 2 and puntaje >=5) or \
            (id_escala == 3 and puntaje >=8):
            cur.execute("""
                SELECT * 
                FROM `actividades` a
                WHERE a.`variable` = %s
            """, 
            [nom_variable])
            actividades = cur.fetchall()

        cur.close()

        return render_template('resultado_test.html', actividades=actividades,
                                                        resultado_test=resultado_test)
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
        if request.method == 'POST':

            id_alumno= session['usuario']['id_alumno']
            # tabla alumno_escala
            p1 = int(request.form['1'])
            p2 = int(request.form['2'])
            p3 = int(request.form['3'])
            p4 = int(request.form['4'])
            p5 = int(request.form['5'])
            p6 = int(request.form['6'])
            p7 = int(request.form['7'])


            puntaje_total=p1+p2+p3+p4+p5+p6+p7
            puntaje_total=int(puntaje_total)
            nivel_variable="Temp"
            desarrollo=datetime.datetime.now()
            desarrollo=desarrollo.strftime('%Y-%m-%d')

            if puntaje_total==4:
                nivel_variable="Leve"
            elif puntaje_total>=5 and puntaje_total<=7:
                nivel_variable="Moderada"
            elif puntaje_total==8 or puntaje_total == 9:
                nivel_variable="Severa"
            elif puntaje_total<4:
                nivel_variable="Sin ansiedad"
            else:
                nivel_variable="Extremadamente Severa"

            cur = mysql.connection.cursor()

            cur.execute(
                "INSERT INTO alumno_escala (id_escala, Ddesarrollo, puntaje, nivel_variable, id_alumno) VALUES (%s,%s,%s,%s,%s)",
                (1, desarrollo, puntaje_total, nivel_variable, id_alumno))
            mysql.connection.commit()

            ruta = url_for('visualizar_resultado', id_alumno_escala=cur.lastrowid)

            print("Se registró la escala correctamente.")
            cur.close()
            return redirect(ruta)
        else:
            return render_template('test_ansiedad.html')
    else:
        print('No usuario')
        return redirect(url_for('login'))
# Test de Depresión
@app.route('/test_depresion', methods=['GET','POST'])
def test_depresion():
    if is_logged():
        if request.method == 'POST':

            id_alumno= session['usuario']['id_alumno']
            # tabla alumno_escala
            p1 = int(request.form['1'])
            p2 = int(request.form['2'])
            p3 = int(request.form['3'])
            p4 = int(request.form['4'])
            p5 = int(request.form['5'])
            p6 = int(request.form['6'])
            p7 = int(request.form['7'])


            puntaje_total=p1+p2+p3+p4+p5+p6+p7
            puntaje_total=int(puntaje_total)
            nivel_variable="Temp"
            desarrollo=datetime.datetime.now()
            desarrollo=desarrollo.strftime('%Y-%m-%d')

            if puntaje_total==5 or puntaje_total == 6:
                nivel_variable="Leve"
            elif puntaje_total>=7 and puntaje_total<=10:
                nivel_variable="Moderada"
            elif puntaje_total>=11 and puntaje_total <= 13:
                nivel_variable="Severa"
            elif puntaje_total<=4:
                nivel_variable="Sin depresión"
            else:
                nivel_variable="Extremadamente Severa"

            cur = mysql.connection.cursor()

            cur.execute(
                "INSERT INTO alumno_escala (id_escala, Ddesarrollo, puntaje, nivel_variable, id_alumno) VALUES (%s,%s,%s,%s,%s)",
                (2, desarrollo, puntaje_total, nivel_variable, id_alumno))
            mysql.connection.commit()
            
            ruta = url_for('visualizar_resultado', id_alumno_escala=cur.lastrowid)

            print("Se registró la escala correctamente.")
            cur.close()
            return redirect(ruta)
        else:
            return render_template('test_depresion.html')
    else:
        print('No usuario')
        return redirect(url_for('login'))

# Test de Estrés
@app.route('/test_estres', methods=['GET','POST'])
def test_estres():
    if is_logged():
        if request.method == 'POST':

            id_alumno= session['usuario']['id_alumno']
            # tabla alumno_escala
            p1 = int(request.form['1'])
            p2 = int(request.form['2'])
            p3 = int(request.form['3'])
            p4 = int(request.form['4'])
            p5 = int(request.form['5'])
            p6 = int(request.form['6'])
            p7 = int(request.form['7'])


            puntaje_total=p1+p2+p3+p4+p5+p6+p7
            puntaje_total=int(puntaje_total)
            nivel_variable="Temp"
            desarrollo=datetime.datetime.now()
            desarrollo=desarrollo.strftime("%Y-%m-%d")

            if puntaje_total==8 or puntaje_total == 9:
                nivel_variable="Leve"
            elif puntaje_total>=10 and puntaje_total<=12:
                nivel_variable="Moderada"
            elif puntaje_total>=13 and puntaje_total <= 16:
                nivel_variable="Severa"
            elif puntaje_total<=7:
                nivel_variable="Sin estrés"
            else:
                nivel_variable="Extremadamente Severa"

            cur = mysql.connection.cursor()

            cur.execute(
                "INSERT INTO alumno_escala (id_escala, Ddesarrollo, puntaje, nivel_variable, id_alumno) VALUES (%s,%s,%s,%s,%s)",
                (3, desarrollo, puntaje_total, nivel_variable, id_alumno))
            mysql.connection.commit()

            ruta = url_for('visualizar_resultado', id_alumno_escala=cur.lastrowid)

            print("Se registró la escala correctamente.")
            cur.close()
            return redirect(ruta)
        else:
            return render_template('test_estres.html')
    else:
        print('No usuario')
        return redirect(url_for('login'))


# Registro Alumno:
@app.route('/registro_alumno', methods=['GET','POST'])
def registro_alumno():
    if request.method == 'POST':

        # tabla persona
        nombres = request.form['nombre']
        apellidos = request.form['apellidos']
        email = request.form['email']
        sede = request.form['sede']
        contrasena = request.form['contrasena']
        # tabla alumno
        carrera = request.form['carrera']
        sexo = request.form['sexo']
        ciclo = request.form['ciclo']
        edad = request.form['edad']

        # Para BD con herencia
        # INSERT INTO persona (nombre, apellidos, email, sede, contrasena) VALUES (%s,%s,%s,%s,%s);
        # BEGIN; INSERT INTO alumno(carrera, sexo, ciclo, edad) VALUES (%s,%s,%s,%s); COMMIT;

        #Para BD sin herencia
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO alumno (carrera, edad, ciclo, nombres, apellidos, email, contrasena, sexo, sede) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (carrera, edad, ciclo, nombres, apellidos, email, contrasena, sexo, sede))
        mysql.connection.commit()
        return redirect(url_for('login'))
    else:
        return render_template('registro_alumno.html')

# Editar Perfil Alumno
@app.route('/editar_perfil_a', methods=['GET','POST'])
def editar_perfil_a():
    if is_logged():
        if request.method == 'POST':

            # ID del alumno
            id_alumno= session['usuario']['id_alumno']

            # tabla persona
            nombres = request.form['nombre']
            apellidos = request.form['apellidos']
            email = request.form['email']
            sede = request.form['sede']
            contrasena = request.form['contrasena']
            # tabla alumno
            carrera = request.form['carrera']
            sexo = request.form['sexo']
            ciclo = request.form['ciclo']
            edad = request.form['edad']

            #Para BD sin herencia
            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE alumno set carrera=%s, edad=%s, ciclo=%s, nombres=%s, apellidos=%s, email=%s, contrasena=%s, sexo=%s, sede=%s WHERE id_alumno=%s",
                (carrera, edad, ciclo, nombres, apellidos, email, contrasena, sexo, sede, id_alumno))
            mysql.connection.commit()
            return redirect(url_for('editar_perfil_a'))
        else:
            return render_template('editar_perfil_a.html')
    else:
        print("No usuario")
        return redirect(url_for('login'))

################################################################################################################################################
#CUALQUIER ERROR ELIMINAR LO QUE ESTE DENTRO DE LOS ASTERISCOS
#Estado Mental
@app.route('/estado_mental', methods=['GET','POST'])
def estado_mental():
    if is_logged():
        cur = mysql.connection.cursor()
        id_alumno = session['usuario']['id_alumno']

        cur.execute("SELECT * FROM alumno_escala WHERE id_alumno = %s", (id_alumno,))
        alumno = cur.fetchall()

        df=pd.DataFrame(alumno, columns=['id_alumno_escala','id_escala', 'Ddesarrollo', 'puntaje','nivel_variable','id_alumno'])
        
        dash_app=dash.Dash(server=app,name="Dashboard", url_base_pathname="/hola/")
        dash_app.layout=html.Div(
                children=[
                    html.H1(children="Gráfico de barras"),
                    html.Div(children="Dash: Graficos"),
                    dcc.Graph(
                        id="Grafico",
                        figure=px.scatter(df, x="id_alumno_escala", y="Ddesarrollo",
                                            size="puntaje", color="id_escala", hover_name="nivel_variable",
                                            log_x=True, size_max=60)               
                    ),
                    html.A(children="Volver", href="/estado_mental"),
                    html.A(children="Cerrar Sesión", href="/logout")
                ]
            )


        return render_template('estado_mental.html')
    else:
        print('no usuario')
        return redirect(url_for('login'))

#DASHBOARD
def create_dash_app(dash_app):
    df=pd.read_csv("test.csv")
    dash_app=dash.Dash(server=app,name="Dashboard", url_base_pathname="/hola2/")
    dash_app.layout=html.Div(
                children=[
                    html.H1(children="Gráfico de barras"),
                    html.Div(children="Dash: Graficos"),
                    dcc.Graph(
                        id="Grafico",
                        figure=px.bar(df, x="nivel_variable", y="Ddesarrollo", barmode="group")                
                    ),
                    html.A(children="Cerrar Sesión", href="/logout")
                ]
            )
    return dash_app
#DashB 2
def create_dash_app2(dash_app):
    df=pd.read_csv("test.csv")
    dash_app=dash.Dash(server=app,name="Dashboard", url_base_pathname="/hola3/")
    dash_app.layout=html.Div(
                children=[
                    html.H1(children="Gráfico de barras"),
                    html.Div(children="Dash: Graficos"),
                    dcc.Graph(
                        id="Grafico",
                        figure=px.bar(df, x="nivel_variable", y="puntaje", barmode="group")               
                    ),
                    html.A(children="Cerrar Sesión", href="/logout")
                ]
            )
    return dash_app

create_dash_app(app)
create_dash_app2(app)

################################################################################################################################################
# registro psicologo:
@app.route('/registro_psi', methods=['GET','POST'])
def registro_psi():
    if request.method == 'POST':
        # tabla persona
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        email = request.form['email']
        sede = request.form['sede']
        contrasena = request.form['contrasena']
        # tabla psicologo
        num_colegiado = request.form['num_colegiado']

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO `psicologo` 
            (`num_colegiado`, `nombres`, `apellidos`, `email`, `contrasena`, `sede`) 
            VALUES
            (%s,%s,%s,%s,%s,%s)
        """,
            [num_colegiado, nombre, apellidos, email, contrasena, sede])

        mysql.connection.commit()
        return redirect(url_for('login'))
    else:
        return render_template('registro_psi.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contrasena = request.form['contrasena']

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
            return redirect(url_for('sesion_alumno'))

        elif psicologo is not None and contrasena == psicologo["contrasena"]:
            session["usuario"] = psicologo
            session["nombre"] = psicologo['nombres']
            session["apellido"] =psicologo['apellidos']
            return redirect(url_for('sesion_psicologo'))

        else:
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/sesion_alumno')
def sesion_alumno():
    if is_logged():
        return render_template('sesion_alumno.html')
    return redirect(url_for('login'))

@app.route('/sesion_psicologo')
def sesion_psicologo():
    if is_logged():
        return render_template('sesion_psicologo.html')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port=3000, debug=True)
