(function ($, undefined) {
    // "use strict";

    /**
     * HSV to RGB color conversion
     *
     * H runs from 0 to 360 degrees
     * S and V run from 0 to 100
     *
     * Ported from the excellent java algorithm by Eugene Vishnevsky at:
     * http://www.cs.rit.edu/~ncs/color/t_convert.html
     */
    function hsvToRgb(h, s, v) {
    	var r, g, b;
    	var i;
    	var f, p, q, t;

    	// Make sure our arguments stay in-range
    	h = Math.max(0, Math.min(360, h));
    	s = Math.max(0, Math.min(100, s));
    	v = Math.max(0, Math.min(100, v));

    	// We accept saturation and value arguments from 0 to 100 because that's
    	// how Photoshop represents those values. Internally, however, the
    	// saturation and value are calculated from a range of 0 to 1. We make
    	// That conversion here.
    	s /= 100;
    	v /= 100;

    	if(s == 0) {
    		// Achromatic (grey)
    		r = g = b = v;
    		return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
    	}

    	h /= 60; // sector 0 to 5
    	i = Math.floor(h);
    	f = h - i; // factorial part of h
    	p = v * (1 - s);
    	q = v * (1 - s * f);
    	t = v * (1 - s * (1 - f));

    	switch(i) {
    		case 0:r = v;g = t;b = p;break;
    		case 1:r = q;g = v;b = p;break;
    		case 2:r = p;g = v;b = t;break;
    		case 3:r = p;g = q;b = v;break;
    		case 4:r = t;g = p;b = v;break;
    		default:r = v;g = p;b = q;
        }

    	return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
    }

    var basicOptions = {
        scales: {
            xAxes: [{
                type: "time",
                ticks: {
                    source: 'labels'
                },
                time: {
                    displayFormats: {
                        "millisecond": "MMM DD",
                        "second": "MMM DD",
                        "minute": "MMM DD",
                        "hour": "MMM DD",
                        "day": "MMM DD",
                        "week": "MMM DD",
                        "month": "MMM DD",
                        "quarter": "MMM DD",
                        "year": "MMM DD",
                    }
                }
            }],
        },
        responsive: true,
    };

    function setupChart($object) {

        var $dataX = $object.data("time");
        var times = [];
        $dataX.forEach(function (element) {
            times.push(window.moment(element));
        });

        var allObjectData = $object.data();
        var data = [];
        // Count how many graphs are displayed
        var nbColors = 0;
        for (var i in allObjectData) {
            if (i.indexOf("views") > -1) {
                nbColors++;
            }
        }
        var n = 0;
        for (var i in allObjectData) {
            if (i.indexOf("views") > -1) {
                var label = $object.data("label-" + i);
                var color = hsvToRgb(n, 100, 80);
                data.push({
                    label: label,
                    data: allObjectData[i],
                    fill: false,
                    backgroundColor: "rgba("+ color.join(',')+ ",0.70)",
                    borderColor: "rgba("+ color.join(',')+ ",0.70)",
                });
                n += 360 / nbColors;
            }
        }

        var config = {
            type: "line",
            data: {
                labels: times,
                datasets: data
            },
            options: basicOptions
        };
        new window.Chart($object, config);
    }

    if ($("#view-graph").length) {
        setupChart($("#view-graph"));
    }
    if ($("#visit-time-graph").length) {
        setupChart($("#visit-time-graph"));
    }


})(jQuery);
