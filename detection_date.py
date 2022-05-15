from sutime import SUTime
import string
#obj_sutime = SUTime(mark_time_ranges=True, include_range=True,language='spanish')
obj_sutime = SUTime(language='spanish')
dias_semana = [ 'lunes', 'martes', 'miércoles','miercoles', 'jueves', 'viernes', 'sabado', 'sábado', 'domingo' ]
meses = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','setiembre','septiembre','octubre','noviembre','diciembre']

def get_date_list(text):
  return obj_sutime.parse(text)

def get_date_by_points(arr_dates):
    maxi, maxpoints = -1, 0
    for index in range(len(arr_dates)):
        obj_date = arr_dates[index]

        ## preprocesamiento del texto
        text_date = obj_date['text'].lower().strip()
        for c in (string.punctuation + ' \n'):
            text_date = text_date.replace(c, " ")
        text_date = text_date.split(' ')
        
        ## Puntaje para la fecha
        points = 0
        for word in text_date:
            if word.isdigit():
                points += 1
            elif word in (dias_semana + meses):
                points += 2

        if points > maxpoints:
            maxi = index
            maxpoints = points
    
    if maxi == -1:
        return None
    return arr_dates[maxi]['value']