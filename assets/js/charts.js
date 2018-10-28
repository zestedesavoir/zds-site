(function ($, undefined) {
    "use strict";

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

        if (s === 0) {
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

        switch (i) {
            case 0: r = v; g = t; b = p; break;
            case 1: r = q; g = v; b = p; break;
            case 2: r = p; g = v; b = t; break;
            case 3: r = p; g = q; b = v; break;
            case 4: r = t; g = p; b = v; break;
            default: r = v; g = p; b = q;
        }

        return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
    }

    var basicOptions = {
        scales: {
            xAxes: [{
                type: "time",
                time: {
                    parser: "DD/MM/YYYY",
                    displayFormats: {
                        "hour": "DD MMM",
                        "day": "DD MMM",
                        "week": "DD MMM",
                        "month": "MMM YYYY",
                        "quarter": "MMM YYYY",
                        "year": "YYYY",
                    }
                }
            }],
            yAxes: [{
                ticks: {
                    beginAtZero: true,
                },
            }],
        },
        responsive: true,
    };

    var charts = new Array();
    function setupChart($object, formatter) {

        var $dataX = $object.data("time");
        var times = [];
        $dataX.forEach(function (element) {
            times.push(window.moment(element).format("DD/MM/YYYY"));
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
        for (var o in allObjectData) {
            if (o.indexOf("views") > -1) {
                var label = $object.data("label-" + o);
                var color = hsvToRgb(n, 100, 80);
                data.push({
                    label: label,
                    data: formatter ? allObjectData[o].map(formatter) : allObjectData[o],
                    fill: false,
                    backgroundColor: "rgba(" + color.join(",") + ", 1)",
                    borderColor: "rgba(" + color.join(",") + ", 0.70)",
                    lineTension: 0,
                });
                n += 360 / nbColors;
            }
        }

        var config = {
            type: localStorage.getItem("graphType"),
            data: {
                labels: times,
                datasets: data
            },
            options: basicOptions
        };
        charts.push(new Chart($object, config));
    }

    // Switching between a graph with lines and a graph with bars
    var switch_to_bar = "Afficher un histogramme";
    var switch_to_line = "Afficher une courbe";

    if(!localStorage.getItem("graphType")) {
        localStorage.setItem("graphType", "line"); // default value
    }

    $("#graph_type_toogle").click(function() {
        if(localStorage.getItem("graphType") === "line") {
            localStorage.setItem("graphType", "bar");
            $(this).text(switch_to_line);
        }
        else {
            localStorage.setItem("graphType", "line");
            $(this).text(switch_to_bar);
        }
        clearCharts();
        drawCharts();
    });
    $("#graph_type_toogle").text(localStorage.getItem("graphType") === "line" ? switch_to_bar : switch_to_line);

    // Clearing charts
    function clearCharts() {
        charts.forEach(function(chart) {
            chart.destroy();
        });
    }

    // Drawing charts
    function drawCharts() {
        if ($("#view-graph").length) {
            setupChart($("#view-graph"));
        }
        if ($("#visit-time-graph").length) {
            setupChart($("#visit-time-graph"), Math.round);
        }
        if ($("#users-graph").length) {
            setupChart($("#users-graph"));
        }
        if ($("#new-users-graph").length) {
            setupChart($("#new-users-graph"));
        }
        if ($("#sessions-graph").length) {
            setupChart($("#sessions-graph"));
        }
    }
    drawCharts();

    // Tab management
    function displayTab(tab) {
        // Hide all the tabs
        $(".tabcontent").each(function () {
            $(this).hide();
        });
        // Remove "active" info from links
        $(".tablinks").each(function () {
            $(this).removeClass("active");
        });
        // Show current tab and add "active" class to the link
        $("#" + $(tab).attr("id") + "-content").show();
        $(tab).addClass("active");
    }

    $(".tablinks").each(function () {
        $(this).click(function () {
            displayTab($(this));
        });
    });
    displayTab($(".tablinks").first());

})(jQuery);
