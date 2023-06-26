from flask import Flask,render_template,request,session,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
import hashlib
from datetime import datetime
from sqlalchemy.sql import text

app=Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key='abcdeFGH'

from models import db
from models import Preceptor,Curso,Estudiante,Asistencia,Padre

@app.route('/')
def inicio():
    session['name']=None
    if not session.get('name'):
        return render_template('inicio.html')

@app.route('/iniciar_sesion', methods=['GET','POST'])
def iniciar_sesion():
    if request.method=="POST":
        if not request.form['email'] or not request.form['password']:
            return render_template('error.html',error='Datos requeridos no ingresados')
        else:
            usuarioActual=None
            if request.form['rol']=='preceptor':
                usuarioActual=Preceptor.query.filter_by(correo=request.form['email']).first()

            elif request.form['rol']=='padre':
                usuarioActual=Padre.query.filter_by(correo=request.form['email']).first()
            if usuarioActual is None:
                return render_template('error.html',error='El email ingresado no se encuentra registrado')
            else:
                clave =  request.form['password']
                result = hashlib.md5(bytes(clave, encoding='utf-8'))
                if request.form['rol']=='preceptor':
                    verificacion=Preceptor.query.filter_by(clave=result.hexdigest()).first()
                elif request.form['rol']=='padre':
                    verificacion=Padre.query.filter_by(clave=result.hexdigest()).first()
                if verificacion:
                    session['name']=request.form['email']
                    datosF=request.form
                    if request.form['rol']=='preceptor':
                        return render_template('preceptor.html',hora=datetime.now().hour,datos=datosF)
                    elif request.form['rol']=='padre':
                        return render_template('padre.html',hora=datetime.now().hour,datos=datosF)
                else:
                    return render_template('error.html',error='La contraseña ingresada no es válida')
        
    return render_template('iniciar_sesion.html')



@app.route('/registrar_asistencia', methods=['GET','POST'])
def registrar_asistencia():
    if request.method == 'POST':
        if not  session['curso']:
            curso_actual=request.form['curso']
            session['curso']=curso_actual
            curso_obtenido=Curso.query.filter_by(id=curso_actual).first()
            estudiantes_obtenidos=Estudiante.query.filter_by(idcurso=curso_obtenido.id).order_by(text('apellido, nombre')).all()
            return render_template('cargar_asistencias.html',estudiantes=estudiantes_obtenidos)
        else:
            if request.form['fecha']:
                fecha=request.form['fecha']
                clase=int(request.form['claseAula'])
                curso_obtenido=Curso.query.filter_by(id=session['curso']).first()
                estudiantes_obtenidos=Estudiante.query.filter_by(idcurso=curso_obtenido.id).order_by(text('apellido, nombre')).all()
                for estudiante in estudiantes_obtenidos:
                    asistencia=request.form.get(f'asistio_{estudiante.id}')
                    justificacion=request.form.get(f'justificacion_{estudiante.id}','')
                    nueva_asistencia=Asistencia(idestudiante=estudiante.id,fecha=datetime.strptime(fecha, "%Y-%m-%d").date(),codigoclase=clase,asistio=asistencia,justificacion=justificacion if asistencia == 'n' else '')
                    db.session.add(nueva_asistencia)
                    db.session.commit()
                return render_template('error.html',mensaje='Asistencia guardada con éxito')
        
    else:
        session['curso']=None
        return render_template('registrar_asistencia.html',preceptor=Preceptor.query.filter_by(correo=session['name']).first())
        


@app.route('/cargar_asistencia')
def cargar_asistencia():
    if request.method == 'POST':
        print('xd')
        if not request.form['fecha']:
            return render_template('error_preceptor.html',error='No se han seleccionado correctamente los datos')
        else:
            clase_actual=int(request.form['clase'])
            fecha_actual=request.form['fecha']
            
            return render_template('carga_exitosa.html')
    else:
        curso_actual=request.form['curso']
        curso_obtenido=Curso.query.filter_by(id=curso_actual).first()
        estudiantes_obtenidos=Estudiante.query.filter_by(idcurso=curso_obtenido.id).order_by(text('apellido, nombre')).all()
        return render_template('cargar_asistencias.html',estudiantes=estudiantes_obtenidos)

@app.route('/mostrar_informe', methods=['GET','POST'])
def mostrar_informe():
    if request.method == 'POST':
        curso_actual=request.form['curso']
        curso_obtenido=Curso.query.filter_by(id=curso_actual).first()
        estudiantes_obtenidos=Estudiante.query.filter_by(idcurso=curso_obtenido.id).order_by(text('apellido, nombre')).all()
        lista_asistencias=[]
        for estudiante in estudiantes_obtenidos:
            contadores=['%s %s'%(estudiante.apellido, estudiante.nombre),0,0,0,0,0,0,0.0]
            asistencias_obtenidas=estudiante.asistencia
            for asistencia in asistencias_obtenidas:
                if asistencia.codigoclase==1:
                    if asistencia.asistio=='s':
                        contadores[1]+=1
                    elif asistencia.asistio=='n':
                        if asistencia.justificacion=='':
                            contadores[2]+=1
                        else:
                            contadores[3]+=1
                elif asistencia.codigoclase==2:
                    if asistencia.asistio=='s':
                        contadores[4]+=1
                    elif asistencia.asistio=='n':
                        if asistencia.justificacion=='':
                            contadores[5]+=1
                        else:
                            contadores[6]+=1
            contadores[7]=float(contadores[2]+contadores[3])+contadores[5]/2+contadores[6]/2
            lista_asistencias.append(contadores)
                
        return render_template('listado_asistencias.html',lista=lista_asistencias)
    else:
        return render_template('obtener_informe.html',preceptor=Preceptor.query.filter_by(correo=session['name']).first())

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('username', None)
    return redirect('/')

if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    session.pop('username', None)