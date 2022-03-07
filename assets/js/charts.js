(function() {
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
    let r, g, b

    // Make sure our arguments stay in-range
    h = Math.max(0, Math.min(360, h))
    s = Math.max(0, Math.min(100, s))
    v = Math.max(0, Math.min(100, v))

    // We accept saturation and value arguments from 0 to 100 because that's
    // how Photoshop represents those values. Internally, however, the
    // saturation and value are calculated from a range of 0 to 1. We make
    // That conversion here.
    s /= 100
    v /= 100

    if (s === 0) {
      // Achromatic (grey)
      r = g = b = v
      return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)]
    }

    h /= 60 // sector 0 to 5
    const i = Math.floor(h)
    const f = h - i // factorial part of h
    const p = v * (1 - s)
    const q = v * (1 - s * f)
    const t = v * (1 - s * (1 - f))

    switch (i) {
      case 0: r = v; g = t; b = p; break
      case 1: r = q; g = v; b = p; break
      case 2: r = p; g = v; b = t; break
      case 3: r = p; g = q; b = v; break
      case 4: r = t; g = p; b = v; break
      default: r = v; g = p; b = q
    }

    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)]
  }

  const basicOptions = {
    scales: {
      x: {
        type: 'time',
        time: {
          parser: 'DD/MM/YYYY',
          tooltipFormat: 'DD/MM/YYYY',
          displayFormats: {
            hour: 'DD MMM',
            day: 'DD MMM',
            week: 'DD MMM',
            month: 'MMM YYYY',
            quarter: 'MMM YYYY',
            year: 'YYYY'
          }
        }
      },
      y: {
        beginAtZero: true
      }
    },
    responsive: true
  }

  const charts = []
  const chartFormatters = {
    'view-graph': null,
    'visit-time-graph': Math.round,
    'users-graph': null
  }
  function setupChart(chartEl, formatter) {
    const dataX = JSON.parse(chartEl.getAttribute('data-time'))
    const times = []
    dataX.forEach(function(element) {
      times.push(window.moment(element).format('DD/MM/YYYY'))
    })

    const allObjectData = chartEl.dataset
    const data = []
    // Count how many graphs are displayed
    let nbColors = 0
    for (const i in allObjectData) {
      if (i.indexOf('views') > -1) {
        nbColors++
      }
    }
    let n = 0
    for (const o in allObjectData) {
      if (o.indexOf('views') > -1) {
        const label = chartEl.getAttribute('data-label-' + o)
        const color = hsvToRgb(n, 100, 80)
        const d = JSON.parse(allObjectData[o])
        data.push({
          label: label,
          data: formatter ? d.map(formatter) : d,
          fill: false,
          backgroundColor: 'rgba(' + color.join(',') + ', 1)',
          borderColor: 'rgba(' + color.join(',') + ', 0.70)',
          lineTension: 0
        })
        n += 360 / nbColors
      }
    }

    const config = {
      type: localStorage.getItem('graphType'),
      data: {
        labels: times,
        datasets: data
      },
      options: {
        ...basicOptions,
        scales: {
          y: {
            title: {
              display: true,
              text: chartEl.getAttribute('data-y-label')
            }
          }
        }
      }
    }
    charts.push(new window.Chart(chartEl, config))
  }

  // Switching between a graph with lines and a graph with bars
  const switchToBar = 'Afficher un histogramme'
  const switchToLine = 'Afficher une courbe'

  if (!localStorage.getItem('graphType')) {
    localStorage.setItem('graphType', 'line') // default value
  }

  const graphTypeToggleEl = document.getElementById('graph_type_toggle')
  if (graphTypeToggleEl !== null) {
    graphTypeToggleEl.addEventListener('click', function() {
      if (localStorage.getItem('graphType') === 'line') {
        localStorage.setItem('graphType', 'bar')
        graphTypeToggleEl.textContent = switchToLine
      } else {
        localStorage.setItem('graphType', 'line')
        graphTypeToggleEl.textContent = switchToBar
      }
      clearCharts()
      drawCharts()
    })
    graphTypeToggleEl.textContent = localStorage.getItem('graphType') === 'line' ? switchToBar : switchToLine
  }

  // Clearing charts
  function clearCharts() {
    charts.forEach(function(chart) {
      chart.destroy()
    })
  }

  // Drawing charts
  function drawCharts() {
    for (const g in chartFormatters) {
      const el = document.getElementById(g)
      if (el !== null) {
        setupChart(el, chartFormatters[g])
      }
    }
  }
  drawCharts()

  // Tab management
  function displayTab(tabEl) {
    if (tabEl === null) {
      return
    }
    // Hide all the tabs
    document.querySelectorAll('.tabcontent').forEach(function(el) {
      el.style.display = 'none'
    })
    // Remove "active" info from links
    document.querySelectorAll('.tablinks').forEach(function(el) {
      el.classList.remove('active')
    })
    // Show current tab and add "active" class to the link
    document.getElementById(tabEl.getAttribute('id') + '-content').style.display = 'block'
    tabEl.classList.add('active')
  }

  document.querySelectorAll('.tablinks').forEach(function(el) {
    el.addEventListener('click', function(e) {
      displayTab(el)
    })
  })
  displayTab(document.querySelector('.tablinks'))
})()
