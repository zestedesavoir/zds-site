const clone = require('clone')
const zmarkdown = require('zmarkdown')
const remarkConfig = require('zmarkdown/remark-config')
const rebberConfig = require('zmarkdown/rebber-config')
const defaultConfig = {remarkConfig, rebberConfig}

// this object is used to memoize processors
const processors = {}

module.exports = function markdownHandlers (Raven) {
  return {
    toHTML,
    toLatex,
    toLatexDocument,
  }

  function toHTML(markdown, opts = {}, callback) {
    if (typeof markdown !== 'string') markdown = String(markdown)

    /* zmd parser memoization */
    const key = JSON.stringify(opts)
    if (!processors.hasOwnProperty(key)) {
      const config = clone(defaultConfig)

      config.remarkConfig.headingShifter = 2

      /* presets */
      if (opts.disable_ping && opts.disable_ping === true) {
        config.remarkConfig.ping.pingUsername = () => false
      }

      if (opts.disable_jsfiddle && opts.disable_jsfiddle === true) {
        config.remarkConfig.iframes['jsfiddle.net'].disabled = true
        config.remarkConfig.iframes['www.jsfiddle.net'].disabled = true
      }

      if (opts.inline && opts.inline === true) {
        config.remarkConfig.disableTokenizers = {
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

      callback(null, [content, metadata])
    })
  }

  function toLatex(markdown, opts = {}, callback) {
    if (typeof markdown !== 'string') markdown = String(markdown)

    /* zmd parser memoization */
    const key = JSON.stringify(opts)
    if (!processors.hasOwnProperty(key)) {
      const config = clone(defaultConfig)

      config.remarkConfig.headingShifter = 0

      if (opts.disable_jsfiddle && opts.disable_jsfiddle === true) {
        config.remarkConfig.iframes['jsfiddle.net'].disabled = true
        config.remarkConfig.iframes['www.jsfiddle.net'].disabled = true
      }

      processors[key] = zmarkdown(config, 'latex')
    }

    processors[key].renderString(String(markdown), (err, content) => {
      if (err) return callback(err, markdown)

      callback(null, [content, {}])
    })
  }

  function toLatexDocument(markdown, opts = {}, callback) {
    toLatex(markdown, opts, (err, [content, metadata]) => {
      if (err) return callback(err)
      const {
        contentType,
        title,
        authors,
        license,
        smileysDirectory,
        disableToc,
        latex = content,
      } = opts
      try {
        const latexDocument = zmarkdown().latexDocumentTemplate({
          contentType,
          title,
          authors,
          license,
          smileysDirectory,
          disableToc,
          latex,
        })
        callback(null, [latexDocument, {}])
      } catch (e) {
        callback(e)
      }
    })
  }
}
