"""
Modulo que contiene las herramientas
y funciones necesarias para calcular
calificaciones, ordenamientos y datos
complementarios de las dependencias
"""
import requests
import datetime
import operator
from collections import OrderedDict
from django.core.cache import cache
from django.conf import settings


MEDALLAS = {'bronce': 1, 'plata': 2, 'oro': 3, 'N/A': 0}
ARRAY_MEDALLAS = {0: 'N/A', 1: 'bronce', 2: 'plata', 3: 'oro'}

#TOTAL_RECURSOS = 0
JSON_DEPENDENCIAS = OrderedDict()
JSON_RECURSOS = OrderedDict()
JSON_RECURSOS_DEPENDENCIAS = OrderedDict()
JSON_DEPENDENCIAS_INFO = OrderedDict()
URL_ADELA = settings.URL_BUDA_API
URL_CKAN = 'https://datos.gob.mx/busca/api/3/action/organization_list'
URL_BUDA_DESCARGAS = 'https://api.datos.gob.mx/v1/google_analytics?pageSize={0}'
KEY_DEPEN = 'resumen-dependendencias'
KEY_RECUR = 'descargas-recursos'
KEY_DEPEND_RECURSOS = 'descargas-recursos-dependencias'
KEY_TOTAL_RECURSOS = 'total-recursos'
KEY_TOTAL_DOWNLOADS = 'descargas-total'
CACHE_TTL = 60 * 60 * 24 * 7


class NetWorkTablero(object):
    """
    Clase estatica que contiene
    las herramientas de networking
    para comunicarse con las APIS
    """
    @staticmethod
    def recuperar_dependencias():
        """
        Funcion que devuelve la lista de dependencias
        del CKAN API
        Retorno: JSON Dict
        """

        respuesta_ckan = requests.get(URL_CKAN)
        dependencias = respuesta_ckan.json()

        return dependencias.get('result', [])

    @staticmethod
    def llamar_a_buda(depen, pagina=1):
        """
        Funcion que consulta el api de BUDA
        Parametro: (String)dependencia, (Int)pagina
        Retorno: Json Dict
        """

        # print(URL_ADELA.format(depen, str(pagina)))
        respuesta_buda = requests.get(URL_ADELA.format(depen, str(pagina)))

        try:
            return respuesta_buda.json()
        except Exception:
            print respuesta_buda.url
            print respuesta_buda
            return None


class NetworkingDownloads(object):
    """
    Clase estatica de conexion
    para el enpoint que trae conteos
    de descargas por recursos
    """

    @staticmethod
    def llamar_buda_conteos(pageSize=10000000):
        respuesta_api = requests.get(URL_BUDA_DESCARGAS.format(pageSize))

        try:
            return respuesta_api.json()
        except Exception:
            return {'results': []}


class MatTableros(object):
    """
    Clase estatica que contiene
    las herramientas para calculos
    matematicos sobre las dependencias
    """
    @staticmethod
    def calcula_total_downloads(objecto):
        """
        Funcion que calcula el total de
        descargas de capturadas por BUDA
        del Analytics
        """
        total = 0;
        for elemento in objecto['results']:
            if elemento.get('value', 0):
                total += elemento['value']
        
        return total

    @staticmethod
    def genera_calificacion(calidad, atrasos, descargas, recomendaciones):
        """
        Funcion genera la calificacion ponderada
        de una dependencia
        Retorno: Int
        """
        calificacion_calidad = {'N/A': 0, 'bronce': 40, 'plata': 50, 'oro': 60}
        calificacion = 0

        print "Atrasos"
        print atrasos
        print "Recomendaciones"
        print recomendaciones
        calificacion += calificacion_calidad[calidad]

        if atrasos is False:
            calificacion += 15

        if descargas:
            calificacion += 15

        if recomendaciones is False:
            calificacion += 10

        return calificacion / 10

    @staticmethod
    def calcula_mediana(muestreo):
        """
        Funcion calcula la mediana
        de un muestreo
        Retorno: Int
        """
        muestreo_ordenado = sorted(muestreo)
        length = len(muestreo_ordenado)
        if not length % 2:
            a_m = muestreo_ordenado[length / 2]
            b_m = muestreo_ordenado[length / 2 - 1]
            return (a_m + b_m) / 2.0

        return muestreo_ordenado[(len(muestreo) / 2)]

    @staticmethod
    def calcula_ranking(deps):
        """
        Funcion calcula el ranking de una
        dependencia en base a sus atributos
        Retorno: Array
        """
        cal = {value: key['calificacion'] for value, key in deps.iteritems()}

        key_oper = operator.itemgetter(1)
        ordenadas = sorted(cal.items(), key=key_oper, reverse=True)

        aux_dep = None
        count_ord = len(ordenadas)

        for elemento in range(0, count_ord):
            # Recorrido de orden exponencial
            for index in range(0, count_ord):
                if elemento < 1:
                    ordenadas[index] = deps[ordenadas[index][0]]

                if index > 0:
                    if ordenadas[index]['calificacion'] == ordenadas[index - 1]['calificacion']:
                        if ordenadas[index]['descargas'] > ordenadas[index - 1]['descargas']:
                            aux_dep = ordenadas[index - 1]
                            ordenadas[index - 1] = ordenadas[index]
                            ordenadas[index] = aux_dep

        # Generamos la respuesta en un arreglo ordenado
        for elemento in range(0, count_ord):
            ordenadas[elemento]['ranking'] = (elemento + 1)

        return ordenadas

    @staticmethod
    def generar_paginacion(dependencia):
        """
        Funcion que calcula el numero
        total de paginas que se debe
        recorrer por dependencia
        Retorno: Json Dict
        Parametro: (String) dependencia
        """
        json_buda = NetWorkTablero.llamar_a_buda(dependencia)

        datos_totales = int(json_buda['pagination']['total'])
        tamano_pagina = int(json_buda['pagination']['pageSize'])

        paginas_totales = (datos_totales / tamano_pagina)
        paginas_totales += 0 if datos_totales % tamano_pagina == 0 else 1

        return range(1, paginas_totales + 1) if paginas_totales > 1 else [1]

    @staticmethod
    def generar_tablero(dependencia):
        """
        Funcion que recorre todos los recursos
        de una dependencia y devuelve
        el resumen de de sus datos
        Parametro: (String) dependencia
        Retorno: Json Dict
        """
        # Valores iniciales
        apertura_array = []
        apertura = 0
        contador = 0
        calidad = 0
        calificacion = 0
        descargas = 0
        recomendaciones = False
        pendientes = False
        nombre_institucion = ''
        publicados = 0
        publicos = 0
        privados = 0
        ligas_no_accesibles = 0
        liga_saludable = True

        # Se obtienen las paginas a recorrer
        vecindario_de_paginas = MatTableros.generar_paginacion(dependencia)
        JSON_RECURSOS_DEPENDENCIAS[dependencia] = []
        JSON_DEPENDENCIAS_INFO[dependencia] = {}
        print "Vecindario"
        print vecindario_de_paginas
        for pagina in vecindario_de_paginas:
            json_buda = NetWorkTablero.llamar_a_buda(dependencia, pagina)

            for recurso in json_buda.get('results', []):
                fecha_act = None
                liga_saludable = True

                if len(recurso['ckan']['resource'].keys()) == 0 and not recurso.get('adela'):
                    continue
            
                if 'name' not in recurso['ckan']['resource'].keys() and not recurso.get('adela'):
                    continue

                # Datos de la dependencia
                if JSON_DEPENDENCIAS_INFO[dependencia].get('slug', None) is None or JSON_DEPENDENCIAS_INFO[dependencia].get('slug', None) == '':
                    if recurso['ckan'].get('dataset', None) and recurso['ckan'].get('dataset', {}).get('organization', None):
                        JSON_DEPENDENCIAS_INFO[dependencia]['slug'] = None if recurso['ckan']['dataset'] is None else recurso['ckan']['dataset']['organization'].get('name', None)
                        JSON_DEPENDENCIAS_INFO[dependencia]['titulo'] = None if recurso['ckan']['dataset'] is None else recurso['ckan']['dataset']['organization'].get('title', None)
                    else:
                        JSON_DEPENDENCIAS_INFO[dependencia]['slug'] = dependencia
                        JSON_DEPENDENCIAS_INFO[dependencia]['titulo'] = dependencia.replace('-', ' ').upper()

                    if JSON_DEPENDENCIAS_INFO[dependencia]['titulo'] == None or JSON_DEPENDENCIAS_INFO[dependencia]['titulo'] == '':
                        JSON_DEPENDENCIAS_INFO[dependencia]['titulo'] = dependencia.replace('-', ' ').upper()

                if recurso.get('calificacion', u'none') != u'none':
                    calidad += MEDALLAS[recurso['calificacion']]
                else:
                    calidad += 1

                if recurso.get('adela'):
                    if recurso['adela']['dataset']['public'] is True:
                        publicos += 1
                    else:
                        privados += 1

                    if recurso['adela']['resource']['modified'] is not None:
                        try:
                            fecha_act = datetime.datetime.strptime(recurso['adela']['resource']['modified'][:16], '%Y-%m-%dT%H:%M')
                        except:
                            pass
                    else:
                        fecha_act = datetime.datetime.strptime(recurso['date-insert'][:16], '%Y-%m-%dT%H:%M')
                else:
                    publicos += 1
                    fecha_act = datetime.datetime.strptime(recurso['date-insert'][:16], '%Y-%m-%dT%H:%M')

                if len(recurso['recommendations']) > 0:
                    recomendaciones = True

                    for recomendacion in recurso['recommendations']:
                        if recomendacion.get('clave') == 'd01':
                            ligas_no_accesibles += 1
                            liga_saludable = False

                try:
                    descargas += recurso['analytics']['downloads']['total'] if recurso['analytics']['downloads']['total'] is not None else 0

                    try:
                        json_recurso = {
                            'recurso': '{0}'.format(recurso['adela']['resource']['title'].encode('utf-8') if recurso.get('adela') else recurso['ckan']['resource']['name'].encode('utf-8')),
                            'descargas': recurso['analytics']['downloads']['total'] if recurso['analytics']['downloads']['total'] is not None else 0,
                            'actualizacion': fecha_act.strftime("%d %b %Y") if fecha_act is not None else None,
                            'organizacion': JSON_DEPENDENCIAS_INFO[dependencia].get('titulo', None) or nombre_institucion,
                            'organizacion_slug': dependencia,
                            'liga_saludable': liga_saludable
                        }
                    except Exception, e:

                        json_recurso = {
                            'recurso': '{0}'.format(recurso['adela']['resource']['title'].encode('utf-8') if recurso.get('adela') else recurso['ckan']['resource']['name'].encode('utf-8')),
                            'descargas': recurso['analytics']['downloads']['total'] if recurso['analytics']['downloads']['total'] is not None else 0,
                            'actualizacion': None,
                            'organizacion': JSON_DEPENDENCIAS_INFO[dependencia].get('titulo', None) or nombre_institucion,
                            'organizacion_slug': dependencia,
                            'liga_saludable': liga_saludable
                        }

                    json_recurso['id'] = '' if recurso['ckan']['resource'] is None or type(recurso['ckan']['resource']) == list else recurso['ckan']['resource'].get('id', None)
                    json_recurso['dataset'] = '' if recurso['ckan']['dataset'] is None else recurso['ckan']['dataset'].get('name', None)

                   # if json_recurso['id'] is None or json_recurso['id'] == '':
                   #     print recurso

                    if json_recurso['id'] != '' and json_recurso['id'] is not None:
                        JSON_RECURSOS_DEPENDENCIAS[dependencia].append(json_recurso)
                        JSON_RECURSOS['{0}'.format(recurso['adela']['resource']['title'].encode('utf-8') if recurso.get('adela') else recurso['ckan']['resource']['name'].encode('utf-8'))] = json_recurso

                except TypeError:
                    descargas += 0
                    JSON_RECURSOS_DEPENDENCIAS[dependencia].append({
                        'recurso': '{0}'.format(recurso['adela']['resource']['title'].encode('utf-8') if recurso.get('adela') else recurso['ckan']['resource']['name'].encode('utf-8')),
                        'descargas': 0,
                        'actualizacion': None
                    })
                    JSON_RECURSOS['{0}'.format(recurso['adela']['resource']['title'].encode('utf-8') if recurso.get('adela') else recurso['ckan']['resource']['name'].encode('utf-8'))] = 0


                if recurso['ckan'].get('resource', None) is not None:
                    publicados += 1
                else:
                    pendientes = True

                try:
                    if not nombre_institucion:
                        nombre_institucion = recurso['ckan']['dataset']['organization']['title']
                except (TypeError, KeyError):
                    nombre_institucion = dependencia
                    pass

                apertura_array.append(recurso['adela']['dataset']['openessRating'] if recurso.get('adela') else 0)
                contador += 1
                #TOTAL_RECURSOS = TOTAL_RECURSOS + 1
                #print TOTAL_RECURSOS

        # Resultados finales
        if len(apertura_array) > 0:
            apertura = int(MatTableros.calcula_mediana(apertura_array))
        else:
            apertura = 0

        if contador == 0:
            contador = 1

        #if len(JSON_RECURSOS_DEPENDENCIAS[dependencia]) != contador:
        #    print "Error en los calculos con JSON_RECURSOS_DEPENDENCIAS"
        #    print "{} vs {}".format(len(JSON_RECURSOS_DEPENDENCIAS[dependencia]), contador)

        #if len(apertura_array) != contador:
        #    print "Error en los calculos con apertura_array"
        #    print "{} vs {}".format(len(apertura_array), contador)

        calidad = ARRAY_MEDALLAS[(calidad/contador)]
        calificacion = MatTableros.genera_calificacion(calidad, pendientes, descargas > 0, recomendaciones)

        return {
            'institucion': JSON_DEPENDENCIAS_INFO[dependencia].get('titulo', None) or nombre_institucion,
            'apertura': apertura,
            'calidad': calidad,
            'descargas': descargas,
            'slug': JSON_DEPENDENCIAS_INFO[dependencia].get('slug', None) or dependencia,
            'total': contador,
            'publicados': publicados,
            'sin-publicar': contador - publicados,
            'calificacion': calificacion,
            'ranking': 0,
            'publicos': publicos,
            'privados': privados,
            'ligas_no_accesibles': ligas_no_accesibles
        } if len(json_buda.get('results', [])) > 1 else {
            'institucion': nombre_institucion or dependencia,
            'apertura': 0,
            'calidad': 'N/A',
            'descargas': 0,
            'publicados': 0,
            'sin-publicar': 0,
            'total': 0,
            'calificacion': 0,
            'ranking': 0,
            'publicos': 0,
            'privados': 0,
            'slug': dependencia,
            'ligas_no_accesibles': ligas_no_accesibles
        }


def scrapear_api_buda():
    """
    Metodo que recorre el API de BUDA
    y obtiene el resumen de cada dependencia
    para guardarlo en cache
    """
    count_dependencias = 0
    for dep in NetWorkTablero.recuperar_dependencias():
        print "Dependencia: {0}".format(dep)
        count_dependencias += 1
        JSON_DEPENDENCIAS[dep] = MatTableros.generar_tablero(dep)

        # if count_dependencias == 10:
            # break

    # Se crea el ranking de las dependencias
    ranking = MatTableros.calcula_ranking(JSON_DEPENDENCIAS)
    total_downloads = MatTableros.calcula_total_downloads(NetworkingDownloads.llamar_buda_conteos())
    # Se guarda en cache por una semana
    cache.set(KEY_DEPEN, ranking, CACHE_TTL)
    cache.set(KEY_RECUR, JSON_RECURSOS, CACHE_TTL)
    cache.set(KEY_DEPEND_RECURSOS, JSON_RECURSOS_DEPENDENCIAS, CACHE_TTL)
    cache.set(KEY_TOTAL_RECURSOS, len(JSON_RECURSOS), CACHE_TTL)
    cache.set(KEY_TOTAL_DOWNLOADS, total_downloads, CACHE_TTL)
    #cache.set(KEY_DEPENDENCIA_INFO, JSON_DEPENDENCIAS_INFO, CACHE_TTL)

    print "************************Terminan calculos*************************************"
    print "DEPENDENCIAS PROCESADAS: {0}".format(str(count_dependencias))
    print "RECURSOS PROCESADOS: {0}".format(len(JSON_RECURSOS))
