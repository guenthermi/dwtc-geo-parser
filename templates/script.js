$(function(){

	$('td.geo-entity').click(function(event){
		$('#map').css('visibility', 'visible');
		$('#osm').html('');
		map = new OpenLayers.Map("osm");
        var mapnik = new OpenLayers.Layer.OSM();
        map.addLayer(mapnik);
        var center = null;
        var markers = new OpenLayers.Layer.Markers( "Markers" );
        map.addLayer(markers);
        var name =  $(this).text();
        $.each(data[$(this).attr('colid')], function(k, v){
    		var lonLat = new OpenLayers.LonLat(v[1],v[0]) // Center of the map
          		.transform(
		            new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
		            new OpenLayers.Projection("EPSG:900913") // to Spherical Mercator Projection
		          );

		markers.addMarker(new OpenLayers.Marker(lonLat));
		if (String(name).localeCompare(String(k)) == 0){
			center = lonLat;
		}
        });

        map.setCenter(center, 1);
		$('div.olControlAttribution').css('bottom', '0px');
		});

	$('.close').click(function(){
		$('#map').css('visibility', 'hidden');
	});
	if (window.location.href.split('#').length > 1){
		window.location.href = '#' + window.location.href.split('#')[1];
	}
});
