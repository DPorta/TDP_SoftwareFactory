import datetime
from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from os import path

from pymysql import NULL

app = Flask(__name__)
# Conexion a sql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
# Nombre de la BD en phpmyadmin
app.config['MYSQL_DB'] = 'tdp_sw_v23'
# CURSOR
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# Configuracion
app.secret_key = '123456'

## Variables
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

# HOME (Página de Inicio)
@app.route('/')
def home():
    return render_template('login.html')

# El usuario esta loggeado
def is_logged():
    if 'usuario' in session:
        return True
    return False

# Registrar horario psicologo
@app.route('/registro_horario', methods=['GET', 'POST'])
def registrar_horario():
    error = None
    if is_logged():
        id_psicologo = session['usuario']['id_psicologo']
        if request.method == 'POST':
            
            fecha = request.form['fecha']
            hora = int(request.form['hora'])

            h_inicio = datetime.timedelta(hours=hora)
            h_fin = datetime.timedelta(hours=hora + 1)
            
            cur = mysql.connection.cursor()

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
                    (`dia`, `h_inicio`, `h_fin`, `id_psicologo`) 
                    VALUES
                    (%s,%s,%s,%s)
                    """,
                    [ fecha, h_inicio, h_fin, id_psicologo ])
                mysql.connection.commit()
                flash('Se registro el horario correctamente.')
            else:
                error='Ya tiene un horario registrado en esa fecha y hora.'
        
        cur = mysql.connection.cursor()
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
                                                        error=error)
    else:
        return redirect(url_for('login'))


# Registrar cita alumno
@app.route('/registro_cita', methods=['POST'])
def registrar_cita():
    if is_logged():
        id_alumno = session['usuario']['id_alumnos']
        
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
            print(resultado_cita)
            print(len(resultado_cita), 'elementos.')
            for r in resultado_cita:
                print(r['id_horario'])
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

            id_alumno= session['usuario']['id_alumnos']
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
            desarrollo=desarrollo.strftime('%Y-%m/%d')

            if puntaje_total<=4:
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
                "INSERT INTO alumno_escala (id_escala, Ddesarrolllo, puntaje, nivel_variable, id_alumnos) VALUES (%s,%s,%s,%s,%s)",
                (1, desarrollo, puntaje_total, nivel_variable, id_alumno))
            mysql.connection.commit()

            flash("Se registró la escala correctamente.")

            return redirect(url_for('test_psicologico_main'))
        else:
            return render_template('test_ansiedad.html')
    else:
        flash('No usuario')
        return redirect(url_for('login'))
# Test de Depresión
@app.route('/test_depresion', methods=['GET','POST'])
def test_depresion():
    if is_logged():
        return render_template('test_depresion.html')
    else:
        print('no usuario')
        return redirect(url_for('login'))

# Test de Estrés
@app.route('/test_estres', methods=['GET','POST'])
def test_estres():
    if is_logged():
        return render_template('test_estres.html')
    else:
        print('no usuario')
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

@app.route('/layout', methods=["GET", "POST"])
def layout():
    # Cerrar sesión (Falta Solucionar)
    #session.clear()
    return render_template('login.html')

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

        # Para BD con herencia
        # cur.execute("SELECT * FROM persona WHERE email= %s", (email,))
        # Para BD sin herencia

        # Alumno
        cur.execute("SELECT * FROM alumno WHERE email= %s", (email,))
        alumno = cur.fetchone()
        
        # Psicologo
        cur.execute("SELECT * FROM psicologo WHERE email= %s", (email,))
        psicologo = cur.fetchone()
        
        cur.close()

        if alumno is not None and contrasena == alumno["contrasena"]:
            session["usuario"] = alumno
            return redirect(url_for('sesion_alumno'))

        elif psicologo is not None and contrasena == psicologo["contrasena"]:
            session["usuario"] = psicologo
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
