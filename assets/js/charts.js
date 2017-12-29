(function ($, undefined) {
    // "use strict";

    var basicOptions = {
        scales: {
            xAxes: [{
                type: "time",
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
        for (var i in allObjectData) {
            if (i.indexOf("views") > -1) {
                var label = $object.data("label-" + i);
                data.push({
                    label: label,
                    data: allObjectData[i],
                });
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
