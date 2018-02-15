// TODO zmd: Implement Sentry monitoring
const clone = require('clone')
const express = require('express')
const bodyParser = require('body-parser')

const zmarkdown = require('zmarkdown')
/* TODO zmd: use proper config for zestedesavoir */
const defaultConfig = require('zmarkdown/config')


const app = express()
app.use(bodyParser.json())

/* temporary fix to prevent tests from hitting the API */
defaultConfig.ping.pingUsername = () => true
/* TODO zmd: above section should be gone by the time we release */

const processors = {}
let times = []
let i = 0
let t = 0

app.post('/latex', (req, res) => {
  toLatex(req.body.md, req.body.opts, (err, result) => {
    res.json(result)
  })
})

app.post('/latex-document', (req, res) => {
  toLatexDocument(req.body.md, req.body.opts, (err, result) => {
    res.json(result)
  })
})

app.post('/html', (req, res) => {
  toHTML(req.body.md, req.body.opts, (err, result) => {
    res.json(result)
  })
})

const server = app.listen(27272, () => {
  const host = server.address().address
  const port = server.address().port

  console.warn("zmarkdown server listening at http://%s:%s", host, port)
})

function toHTML(markdown, opts = {}, callback) {
  const s = Date.now()

  if (typeof markdown !== 'string') markdown = String(markdown)

  /* if this zmd parser doesn't exist, we create it with the right config */
  const key = JSON.stringify(opts)
  if (!processors.hasOwnProperty(key)) {
    const config = clone(defaultConfig)

    config.headingShifter = 2

    /* presets */
    if (opts.disable_ping && opts.disable_ping === true) {
      config.ping.pingUsername = () => false
    }

    if (opts.disable_jsfiddle && opts.disable_jsfiddle === true) {
      config.iframes['jsfiddle.net'].disabled = true
      config.iframes['www.jsfiddle.net'].disabled = true
    }

    if (opts.inline && opts.inline === true) {
      config.disableTokenizers = {
        block: [
          'indentedCode',
          'fencedCode',
          'blockquote',
          'atxHeading',
          'setextHeading',
          'footnote',
          'table',
          'custom_blocks'
        ]
      }
    }

    processors[key] = zmarkdown(config, 'html')
  }

  processors[key].renderString(String(markdown), (err, {content, metadata}) => {
    if (err) return callback(err, markdown)

    i += 1
    times.push(Date.now() - s)

    if (i % 500 === 0) {
      i = 0
      t += 1
      console.log(`${t * 500} avg`, times.reduce((sum, value) => sum + value, 0) / 500)
      times = []
    }

    callback(null, [content, metadata])
  })
}

function toLatex(markdown, opts = {}, callback) {
  const s = Date.now()
  if (typeof markdown !== 'string') markdown = String(markdown)

  /* if this zmd parser doesn't exist, we create it with the right config */
  const key = JSON.stringify(opts)
  if (!processors.hasOwnProperty(key)) {
    const config = clone(defaultConfig)

    config.headingShifter = 0
    config.ping.pingUsername = () => false

    if (opts.disable_jsfiddle && opts.disable_jsfiddle === true) {
      config.iframes['jsfiddle.net'].disabled = true
      config.iframes['www.jsfiddle.net'].disabled = true
    }

    processors[key] = zmarkdown(config, 'latex')
  }

  processors[key].renderString(String(markdown), (err, content) => {
    if (err) return callback(err, markdown)

    callback(null, [content, {}])
  })
}


function toLatexDocument(markdown, opts = {}, callback) {
  console.log({markdown})
  toLatex(markdown, opts, (err, [content, metadata]) => {
    if (err) return callback(err)
    const {
      contentType,
      title,
      authors,
      license,
      smileysDirectory,
      toc = true,
      latex = content,
    } = opts
    try {
      const latexDocument = zmarkdown().latexDocumentTemplate({
        contentType,
        title,
        authors,
        license,
        smileysDirectory,
        toc,
        latex,
      })
      callback(null, [latexDocument, {}])
    } catch (e) {
      callback(e)
    }
  })
}

