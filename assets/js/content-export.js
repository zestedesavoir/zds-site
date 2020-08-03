/* ===== Zeste de Savoir ====================================================
   Exports modale: opening and live-update.
   ---------------------------------
   Author: Amaury Carrade
   ========================================================================== */

(function() {
  const exportsModal = document.getElementById('exports-modal')

  // Not on a tutorial page
  if (!exportsModal) return

  const exportsModalHandle = document.querySelector('[data-exports-api]')

  const exportsSection = exportsModal.querySelector('section.exports')
  const exportsRequestButton = exportsModal.querySelector('footer button.btn')

  const exportsAPI = exportsModalHandle.dataset.exportsApi
  const exportRequestAPI = exportsModalHandle.dataset.requestExportApi

  const t = exportsSection.dataset

  const formatter = new Intl.DateTimeFormat('fr-FR', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  })

  const formatterLong = new Intl.DateTimeFormat('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    second: 'numeric'
  })

  exportsRequestButton.dataset.initialLabel = exportsRequestButton.innerText

  /**
   * Displays a message where the exports list stands (removing the list),
   * e.g. to display an error message, or if the list is empty.
   */
  function displayError(message) {
    exportsSection.classList.add('is-empty')

    const p = document.createElement('p')
    p.innerHTML = message

    exportsSection.innerHTML = ''
    exportsSection.appendChild(p)
  }

  /**
   * Calls the exports API and update the view with the current exports and
   * their statuts.
   */
  function updateExports() {
    return fetch(exportsAPI)
      .then(response => response.json())
      .then(contentExports => {
        if (contentExports.length === 0) {
          displayError(t.trNoExports)
          return
        }

        // We want PDF and ePub first, in this order
        const firstFormats = ['pdf', 'epub']

        contentExports.sort((a, b) => {
          const aIndex = firstFormats.indexOf(a.format_requested)
          const bIndex = firstFormats.indexOf(b.format_requested)
          const aIn = aIndex !== -1
          const bIn = bIndex !== -1

          if (aIn && !bIn) return -1
          else if (!aIn && bIn) return 1
          else if (aIn && bIn) return aIndex - bIndex
          else return a.format_requested.localeCompare(b.format_requested)
        })

        exportsSection.classList.remove('is-empty')
        exportsSection.innerHTML = ''

        for (const contentExport of contentExports) {
          const article = document.createElement('article')
          const header = document.createElement('header')
          const headerH4 = document.createElement('h4')
          const headerP = document.createElement('p')
          const footer = document.createElement('footer')

          const state = contentExport.state_of_processing.toLowerCase()
          const date = new Date(contentExport.date)

          article.classList.add('export')
          article.classList.add(`is-${state}`)

          headerH4.innerText = t['trFormat' + contentExport.format_requested] || contentExport.format_requested

          headerP.setAttribute('title', formatterLong.format(date))
          headerP.innerText = formatter.format(date) + (state === 'success' ? ' – ' : '')

          if (state === 'success') {
            const headerDownloadLink = document.createElement('a')

            headerDownloadLink.setAttribute('title', t.trDownloadTitle)
            headerDownloadLink.innerText = t.trDownload
            headerDownloadLink.setAttribute('href', contentExport.url)

            headerP.appendChild(headerDownloadLink)
          }

          footer.innerText = t[`trState${state}`]

          header.appendChild(headerH4)
          header.appendChild(headerP)

          article.appendChild(header)
          article.appendChild(footer)

          exportsSection.appendChild(article)
        }

        scheduleNextUpdate(contentExports)
      })
      .catch(() => {
        displayError(t.trErrorLoading)
        scheduleNextUpdate()
      })
  }

  /**
   * Schedules the next update task, if it should run.
   * The task should run:
   * - if the modale is open; and
   * - if there is at least one export with state `REQUESTED` or `RUNNING`.
   */
  function scheduleNextUpdate(contentExports) {
    let shouldRun = exportsModal.classList.contains('open')
    if (contentExports) {
      shouldRun &= contentExports
        .filter(exp => exp.state_of_processing === 'REQUESTED' || exp.state_of_processing === 'RUNNING')
        .length > 0
    }

    if (shouldRun) {
      setTimeout(updateExports, 4000)
    }
  }

  /**
   * Displays a message on the “request all exports” button, and disables said
   * button, during the given timeout. After this timeout, the button is
   * restored to its original state.
   */
  function messageOnButton(message, timeout) {
    exportsRequestButton.classList.remove('disabled')
    exportsRequestButton.classList.remove('submitted')

    exportsRequestButton.setAttribute('disabled', 'disabled')
    exportsRequestButton.innerText = message

    setTimeout(() => {
      exportsRequestButton.removeAttribute('disabled')
      exportsRequestButton.innerText = exportsRequestButton.dataset.initialLabel
    }, 1000 * timeout)
  }

  /**
   * Requests the exports to be generated.
   * Sends the POST request, then update the exports list to reflect the
   * request.
   */
  function requestExports() {
    exportsRequestButton.setAttribute('disabled', 'disabled')
    exportsRequestButton.classList.add('disabled')
    exportsRequestButton.classList.add('submitted')
    exportsRequestButton.innerText = t.trGenerationWaiting

    const line = document.createElement('div')
    line.classList.add('line-loading')

    exportsRequestButton.appendChild(line)

    fetch(exportRequestAPI, {
      method: 'POST',
      headers: new Headers({
        'X-CSRFToken': exportsRequestButton.dataset.csrf
      })
    }).then(() => {
      messageOnButton(t.trGenerationRequested, 120)
      updateExports()
    }).catch(e => {
      console.error('Cannot request exports update', e)
      messageOnButton(t.trGenerationErrored, 5)
    })
  }

  exportsModalHandle.addEventListener('click', () => {
    updateExports()
    exportsModalHandle.blur()
  })

  exportsRequestButton.addEventListener('click', requestExports)
})()
