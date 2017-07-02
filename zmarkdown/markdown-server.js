'use strict'

const clone = require('clone')
const zerorpc = require('zerorpc')
const zmarkdown = require('zmarkdown')
const defaultConfig = require('zmarkdown/config')

/* temporary fix to prevent tests from hitting the API */
defaultConfig.ping.pingUsername = () => true
/* TODO: above section should be gone by the time we release */

const heartbeat = 5000
const streaming = false
let i = 0
let t = 0

const processors = {}
let times = []

const server = new zerorpc.Server({
  toHTML: function toHTML(markdown, opts = {}, reply) {
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
      if (err) return reply(err, markdown, streaming)

      i += 1
      times.push(Date.now() - s)

      if (i % 500 === 0) {
        i = 0
        t += 1
        console.log(`${t * 500} avg`, times.reduce((sum, value) => sum + value, 0) / 500)
        times = []
      }
      reply(null, [content, metadata], streaming)
    })
  },
}, heartbeat)

server.bind('tcp://0.0.0.0:24242')
