/* eslint-disable no-console */
const express = require('express')
const bodyParser = require('body-parser')
const {dirname, join} = require('path')

const zmdVersion = require(join(dirname(require.resolve('zmarkdown')), 'package.json')).version

const git = require('git-rev')

const Raven = require('raven')
Raven.config(process.env.SENTRY_DSN, {
  release: zmdVersion,
  environment: process.env.SENTRY_ENVIRONMENT || process.env.ZDS_ENVIRONMENT
}).install()

git.long((commit) => {
  Raven.mergeContext({
    release: process.env.SENTRY_RELEASE || zmdVersion,
    tags: {
      'zds-site_git-commit': commit,
    }
  })

  serverStart()
})

function serverStart () {
  const {
    toHTML,
    toLatex,
    toLatexDocument,
  } = require('./markdown-handlers')(Raven)

  const app = express()

  app.use(Raven.requestHandler())
  app.use(Raven.errorHandler())

  app.use(bodyParser.json())
  app.post('/latex', controllerFactory(toLatex))
  app.post('/latex-document', controllerFactory(toLatexDocument))
  app.post('/html', controllerFactory(toHTML))

  const server = app.listen(27272, () => {
    const host = server.address().address
    const port = server.address().port

    console.warn('zmarkdown server listening at http://%s:%s', host, port)
  })
}

function controllerFactory (handler) {
  return (req, res) => {
    handler(req.body.md, req.body.opts, (err, result) => {
      if (err) {
        Raven.captureException(err, {req})
        res.status(500).json(null)
        return
      }

      res.json(result)
    })
  }
}
