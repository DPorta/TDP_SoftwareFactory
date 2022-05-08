from wtforms import Form, BooleanField, StringField, EmailField, PasswordField, validators, ValidationError, SelectField, IntegerField
import email_validator


def requerido(form, field):
  if not field.data:
    raise ValidationError('El campo es requerido')

def numero_entero(form, field):
  if field.data:
    number=None
    try:
      number = int(field.data)
    except ValueError:
      raise ValidationError('El campo debe ser un numero entero valido.')
    
    if number <= 0 or number >= 100:
      raise ValidationError('El numero debe ser positivo y menor que 100.')

def all_is_digit(form, field):
  if field.data and not field.data.isdigit():
    raise ValidationError('El campo debe ser un digito valido.')

class AlumnoRegForm(Form):
  nombres = StringField('Nombres',
                        validators=[requerido
                                    ]
                        )

  apellidos = StringField('Apellidos', 
                        [requerido
                        ]
                        )

  email = StringField('Email', 
                        validators=[requerido, validators.email('El campo debe ser un correo valido.')
                                    ]
                        )

  contrasena = PasswordField('Contraseña', 
                        [requerido
                        ]
                        )
  carrera = SelectField('Carrera', 
                        choices=[('Ingenieria de sistemas de información', 'Ingenieria de sistemas de información'),('Ingenieria de software','Ingenieria de software'),('Ciencias de la Computación','Ciencias de la Computación')],
                        validators=[requerido]
                      )
  sede = SelectField('Sede', 
                      choices=[('San Miguel', 'San Miguel'),
                              ('San Isidro','San Isidro'),('Monterrico','Monterrico'),
                              ('Villa','Villa')],
                      validators=[requerido]
                      )
  ciclo = SelectField('Ciclo', 
                      choices=[('1ro','1ro'),
                                ('2do','2do'),
                                ('3ro','3ro'),
                                ('4to','4to'),
                                ('5to','5to'),
                                ('6to','6to'),
                                ('7mo','7mo'),
                                ('8vo','8vo'),
                                ('9no','9no'),
                                ('10mo','10mo')
                              ],
                      validators=[requerido]
                      )
  sexo = SelectField('Genero', 
                      choices=[('Masculino','Masculino'),
                                ('Femenino','Femenino'),
                              ],
                      validators=[requerido]
                    )
  edad = StringField('Edad', 
                      validators=[requerido, 
                                  numero_entero]
                    )

class PsicoRegForm(Form):
  nombres = StringField('Nombres',
                        validators=[requerido
                                    ]
                        )

  apellidos = StringField('Apellidos', 
                        [requerido
                        ]
                        )

  email = StringField('Email', 
                        validators=[requerido, validators.email('El campo debe ser un correo valido.')
                                    ]
                        )

  contrasena = PasswordField('Contraseña', 
                        [requerido
                        ]
                        )
  sede = SelectField('Sede', 
                      choices=[('San Miguel', 'San Miguel'),
                              ('San Isidro','San Isidro'),('Monterrico','Monterrico'),
                              ('Villa','Villa')],
                      validators=[requerido]
                      )
  num_colegiado = StringField('Numero Colegiado',
                        validators=[requerido, 
                                    all_is_digit
                                    ]
                        )
