"""
Modulo que controla
las vistas de la aplicacion
"""
import operator
from django.shortcuts import render
from django.core.cache import cache
from django.conf import settings
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from .buda_tools import scrapear_api_buda


def tabla_comparativa(request):
    """
    Vista principal de la tabla
    de instituciones y resumen de
    calificaciones de las mimas
    URL: /tablero-instituciones/
    """
    total_downloads = cache.get('descargas-total', 0)
    return render(request, 'tabla-comparativa.html', {'settings': settings, 'total_downloads': total_downloads})


def detalle_institucion(request, slug=''):
    """
    Vista detalle de una institucion
    en calificaciones y estadisticas
    URL: /tablero-instituciones/detalle-institucion/{slug}/
    """
    template = 'detalle-dependencia.html'
    return render(request, template, {'settings': settings, 'slug': slug})


def genera_resumen_dependencias(request):
    """
    Vista que renueva el resumen
    de las varibales de las dependencias
    URL: /tablero-instituciones/generar-resumen/
    RESPUESTA: Json
    Metodo Http: POST
    """
    if request.method != 'POST':
        raise Http404

    scrapear_api_buda()
    return JsonResponse({'status': 'ok'})


@csrf_exempt
def api_comparativa(request):
    """
    Vista que retorna el calculo
    de las varibales de las dependencias
    URL: /tablero-instituciones/apicomparativa/
    RESPUESTA: Json
    """
    dependencias_cache = cache.get('resumen-dependendencias', {'descargas': []})
    dependencias_cache.sort(key=lambda x: x['descargas'], reverse=True)
    return JsonResponse({'dependencias': dependencias_cache})


@csrf_exempt
def api_comparativa_dependencia(request, slug):
    """
    Vista que retorna el calculo
    de las varibales de una
    dependencia especifica
    URL: /tablero-instituciones/apicomparativa/{slug}/
    RESPUESTA: Json
    """
    dependencias_cache = cache.get('resumen-dependendencias', [])

    try:
        for elemento in dependencias_cache:
            if elemento['slug'] == slug:
                return JsonResponse(elemento)
    except Exception:
        raise Http404
    else:
        raise Http404


@csrf_exempt
def recursos_mas_descargados(request):
    """
    Vista que retorna el Top 5
    de recursos mas descargados
    URL: tablero-instituciones/apicomparativa/recursos-mas-descargados/
    RESPUESTA: Json
    """
    recursos = cache.get('descargas-recursos', None)
    recursos_ordenados = recursos_ordenados_aux = []
    ordenador = {}

    if recursos is not None:
        for key, value in recursos.items():
            ordenador[key] = value['descargas']

        ky = operator.itemgetter(1)
        recursos_ordenados_aux = sorted(ordenador.items(), key=ky, reverse=True)[:5]

        recursos_ordenados = [[recursos[key[0]]['recurso'], recursos[key[0]]['descargas'], recursos[key[0]]['id'], recursos[key[0]]['dataset'], recursos[key[0]]['organizacion']] for key in recursos_ordenados_aux]

    return JsonResponse({'recursos': recursos_ordenados}, safe=False)


@csrf_exempt
def recursos_mas_descargados_dep(request, slug):
    """
    Vista que retorna el Top 5
    de recursos mas descargados
    de una dependencia
    URL: tablero-instituciones/apicomparativa/recursos-mas-descargados/{slug}/
    RESPUESTA: Json
    """
    recursos_ordenados = cache.get('descargas-recursos-dependencias-{0}'.format(slug))

    if not recursos_ordenados:
        recursos = cache.get('descargas-recursos-dependencias', None)
        recursos_ordenados = []

        if recursos is not None:
            try:
                rec_dep = recursos[slug]
            except Exception:
                raise Http404

            recursos_ordenados = sorted(rec_dep, key=lambda x: x['descargas'], reverse=True)
            cache.set('descargas-recursos-dependencias-{0}'.format(slug), recursos_ordenados, 60 * 5)

    return JsonResponse({'recursos': recursos_ordenados}, safe=False)


@csrf_exempt
def total_de_recursos(request):
    """
    Vista que el total de recursos
    contabilizados
    URL: tablero-instituciones/apicomparativa/total-recursos/
    RESPUESTA: Json
    """
    return JsonResponse({'total': cache.get('total-recursos', 0)})
