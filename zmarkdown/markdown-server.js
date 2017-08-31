const express = require('express')
const bodyParser = require('body-parser')

const Raven = require('raven')
Raven.config(process.env.SENTRY_DSN).install();

const {
  toHTML,
  toLatex,
  toLatexDocument,
} = require('./markdown-handlers')(Raven)

const app = express()

app.use(Raven.requestHandler())
app.use(Raven.errorHandler());

app.use(bodyParser.json())
app.post('/latex', controllerFactory(toLatex))
app.post('/latex-document', controllerFactory(toLatexDocument))
app.post('/html', controllerFactory(toHTML))

const server = app.listen(27272, () => {
  const host = server.address().address
  const port = server.address().port

  console.warn("zmarkdown server listening at http://%s:%s", host, port)
})

function controllerFactory (handler) {
  return (req, res) => {
    handler(req.body.md, req.body.opts, (err, result) => {
      if (err) {
        console.error(err)
        res.status(500).send(err)
      }
      res.json(result)
    })
  }
}
