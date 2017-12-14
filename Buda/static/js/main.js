$(document).ready(function() {

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    var urlDescargasDatos = '/tablero-instituciones/apicomparativa/recursos-mas-descargados/';
    var newDataSet, descargasDatos;
    //Datos mas descargados
    $.ajax({
      url: urlDescargasDatos,
      // async: false,
      type: 'POST',
      success: function(data) {
        if(data.recursos === null){
          alert('Sentimos los incovenientes. Estamos actualizando los datos. Intenta mas tarde.');
          return false;
        }
        console.log(data);
        $.each(data.recursos, function(key, value){
          var htmlDatos = '';
          htmlDatos += '<tr><td class="datosTitle" title="'+value[0]+'"><a href="https://datos.gob.mx/busca/dataset/' + value[3] + '/resource/' + value[2] + '" style="width: 345px;" >' + value[0] + '</a></td><td class="text-center datos-institucion">' + value[4].toLocaleString('en') + '</td></tr>';
          $('#table-datos tr').last().after(htmlDatos);
        });
      },
      error: function(){
        alert('Sentimos los incovenientes. Estamos actualizando los datos. Intenta mas tarde.');
        return false;
      }
    });

    $.ajax("https://api.datos.gob.mx/v1/resources?pageSize=1")
       .done(function(data){
        $("#resourcesTotal").html(data.pagination.total.toLocaleString('en'));
      })
       .fail(function(err){
         console.log(err);
      });
    //$('[data-toggle="tooltip"]').tooltip();

    var urlDataSet = '/tablero-instituciones/apicomparativa/';
    var downTotal = 0;
    var resourTotal = 0;
    
    $('#apf_table').dataTable({
      "language": {
          "paginate": {
            "previous": "Anterior",
            "next": "Siguiente",
          },
          "emptyTable": "No se encontraron resultados",
          "zeroRecords": "No se encontraron resultados",
          "sZeroRecords": "No se encontraron resultados",
          "infoEmpty": "No se encontraron resultados"
        },
      "info": false,
      "bLengthChange": false,
      "fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
        $('td:eq(0)', nRow).addClass("depenTitle").attr("title",aData.institucion).attr("tag", aData.slug);
        $('td:eq(1), td:eq(2), td:eq(4)', nRow).addClass("text-center");
        $('td:eq(3), td:eq(2), td:eq(4)', nRow).addClass("text-center");
      },
      "pagingType": "simple_numbers",
      "order": [[ 0, "asc" ]],
      drawCallback: function(settings){
            var api = this.api();
            // Initialize custom control
            initRating(api.table().container());
        },
      "ajax": {
        "url": urlDataSet,
        // "async": false,
        "type": 'POST',
        "dataSrc": function ( json ) {
          if(json.dependencias === null){
            alert('Sentimos los incovenientes. Estamos actualizando los datos. Intenta mas tarde.');
            return false;
          }
          function sortJSON(data, key) {
            return data.sort(function (a, b) {
                var x = a[key];
                var y = b[key];
                return ((x < y) ? -1 : ((x > y) ? 1 : 0));
            });
          }

          var top5Down = sortJSON(json.dependencias, 'descargas');
          
          $.each(top5Down,function(key, value){
            var totalItems = top5Down.length;
            top1 = top5Down[totalItems-1];
            top2 = top5Down[totalItems-2];
            top3 = top5Down[totalItems-3];
            top4 = top5Down[totalItems-4];
            top5 = top5Down[totalItems-5];
          });

          var htmlDown = '';
          htmlDown += '<tr><td class="datosTitle" title="'+top1.institucion+'"><a href="https://datos.gob.mx/busca/organization/' + top1.slug + '">' + top1.institucion + '</a></td><td class="text-center">' + top1.descargas.toLocaleString('en') + '</td></tr>';
          htmlDown += '<tr><td class="datosTitle" title="'+top2.institucion+'"><a href="https://datos.gob.mx/busca/organization/' + top2.slug + '">' + top2.institucion + '</a></td><td class="text-center">' + top2.descargas.toLocaleString('en') + '</td></tr>';
          htmlDown += '<tr><td class="datosTitle" title="'+top3.institucion+'"><a href="https://datos.gob.mx/busca/organization/' + top3.slug + '">' + top3.institucion + '</a></td><td class="text-center">' + top3.descargas.toLocaleString('en') + '</td></tr>';
          htmlDown += '<tr><td class="datosTitle" title="'+top4.institucion+'"><a href="https://datos.gob.mx/busca/organization/' + top4.slug + '">' + top4.institucion + '</a></td><td class="text-center">' + top4.descargas.toLocaleString('en') + '</td></tr>';
          htmlDown += '<tr><td class="datosTitle" title="'+top5.institucion+'"><a href="https://datos.gob.mx/busca/organization/' + top5.slug + '">' + top5.institucion + '</a></td><td class="text-center">' + top5.descargas.toLocaleString('en') + '</td></tr>';
          $('#table-downloads tr').last().after(htmlDown);

          $.each(json.dependencias,function(key, value){
            downTotal = downTotal + value.descargas;
            resourTotal = resourTotal + value.total;
            // $("#downloadsTotal").html(downTotal.toLocaleString('en'));
            //$("#resourcesTotal").html(resourTotal.toLocaleString('en'));
            $("#dependencesTotal").html(json.dependencias.length);
          });

          return json.dependencias;
        }
      },"error": function(){
        alert('Sentimos los incovenientes. Estamos actualizando los datos. Intenta mas tarde.');
        return false;
      },
      "columns": [
          { "data": "institucion", "width": 400 },
          { "data": "publicados", render: $.fn.dataTable.render.number( ',', '.', 0 ), "width": 200 },
          { "data": "descargas", render: $.fn.dataTable.render.number( ',', '.', 0 ), "width": 200 },
          { "data": "ligas_no_accesibles", "width": 200 }
      ],
       columnDefs: [
            { width: 200, targets: 0 },
            { width: 200, targets: 0 },
            { width: 200, targets: 0 },
            { width: 200, targets: 0 }
        ],
        fixedColumns: true
    });

    $("#searchbox").keyup(function() {
        $('#apf_table').dataTable().fnFilter(this.value);
        //table.draw();
    });

    // Initializes jQuery Raty control
    function initRating(container){
      $('.rating', container).raty({
        starType: 'i',
        hints: ['1', '2', '3', '4', '5'],
        half: true,
        starHalf: 'glyphicon glyphicon-star gly-2x',
        starOff: 'glyphicon glyphicon-star-empty gly-2x',
        starOn: 'glyphicon glyphicon-star gly-2x',
        readOnly: true,
        score: function() {
            return $(this).attr('data-score');
        }
      })
    };

    $('#apf_table tbody').on('click', 'tr', function () {
        var titleVar = $(this).find(".depenTitle").attr('tag');
        window.location.href = "/tablero-instituciones/detalle/" + titleVar + "/";
    });

});
