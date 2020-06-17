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
        weekday: "long", year: "numeric", month: "long", day: "numeric"
    })

    const formatterLong = new Intl.DateTimeFormat('fr-FR', {
        weekday: "long", year: "numeric", month: "long", day: "numeric",
        hour: "numeric", minute: "numeric", second: "numeric"
    })

    let updateTaskID = null

    exportsRequestButton.dataset.initialLabel = exportsRequestButton.innerText

    function displayError(message) {
        exportsSection.classList.add('is-empty')

        let p = document.createElement('p');
        p.innerHTML = message;

        exportsSection.innerHTML = ''
        exportsSection.appendChild(p)
    }

    function updateExports() {
        return fetch(exportsAPI)
            .then(response => response.json())
            .then(content_exports => {
                if (content_exports.length === 0) {
                    displayError(t.trNoExports)
                    return
                }

                // We want PDF and ePub first, in this order
                const firstFormats = ['pdf', 'epub']

                content_exports.sort((a, b) => {
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

                for (const content_export of content_exports) {
                    const article = document.createElement('article')
                    const header = document.createElement('header')
                    const headerH4 = document.createElement('h4')
                    const headerP = document.createElement('p')
                    const headerDownloadLink = document.createElement('a')
                    const footer = document.createElement('footer')

                    const state = content_export.state_of_processing.toLowerCase()
                    const date = new Date(content_export.date)

                    article.classList.add('export')
                    article.classList.add(`is-${state}`)

                    headerH4.innerText = t['trFormat' + content_export.format_requested] || content_export.format_requested

                    headerP.setAttribute('title', formatterLong.format(date))
                    headerP.innerText = formatter.format(date) + ' – '

                    if (state === 'success') {
                        headerDownloadLink.setAttribute('title', t.trDownloadTitle)
                    }
                    else if (state === 'running' || state === 'requested') {
                        headerDownloadLink.setAttribute('title', t.trDownloadUnavailableTitle)
                    }
                    else {
                        headerDownloadLink.setAttribute('title', t.trRestartTitle)
                        let restarRequestClicked = false
                        headerDownloadLink.addEventListener('click', () => {
                            if (restarRequestClicked) return;

                            headerDownloadLink.innerText = t.trGenerationWaiting
                            restarRequestClicked = true

                            requestExports()
                        })
                    }

                    if (state === 'failure') {
                        headerDownloadLink.innerText = t.trRestart
                        headerDownloadLink.setAttribute('href', '#')
                    }
                    else {
                        headerDownloadLink.innerText = t.trDownload
                        headerDownloadLink.setAttribute('href', content_export.url)
                    }

                    footer.innerText = t[`trState${state}`]

                    headerP.appendChild(headerDownloadLink)
                    header.appendChild(headerH4)
                    header.appendChild(headerP)

                    article.appendChild(header)
                    article.appendChild(footer)

                    exportsSection.appendChild(article)
                }

                scheduleNextUpdate(content_exports)
            })
            .catch(() => {
                displayError(t.trErrorLoading)
                scheduleNextUpdate()
            })
    }

    /**
     * Starts/stops the update task if required.
     * The task should run:
     * - if the modale is open;
     * - if there is at least one export with state `REQUESTED` or `RUNNING`.
     */
    function scheduleNextUpdate(content_exports) {
        let shouldRun = exportsModal.classList.contains('open')
        if (content_exports) {
            shouldRun &= content_exports
                .filter(exp => exp.state_of_processing === 'REQUESTED' || exp.state_of_processing === 'RUNNING')
                .length > 0
        }

        if (shouldRun) {
            setTimeout(updateExports, 4000)
        }
    }

    function requestExports() {
        exportsRequestButton.setAttribute('disabled', 'disabled')
        exportsRequestButton.classList.add('disabled')
        exportsRequestButton.classList.add('submitted')
        exportsRequestButton.innerText = t.trGenerationWaiting

        const line = document.createElement('div')
        line.classList.add('line-loading')

        exportsRequestButton.appendChild(line)

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

        let headers = new Headers()

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
