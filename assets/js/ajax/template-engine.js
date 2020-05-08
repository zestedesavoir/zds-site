/**
 * @name Simple template engine
 * @version: 1.0
 * @Author: A-312
 */


/*

# Simple moteur de template

## Comportement

Au chargement de la page le script parcours tous les template[tpl-request]. Chaque template doit
être d'un type prédéfini via l'attribut `tpl-type`.

L'api à l'url `tpl-request` va être interrogée toutes les `tpl-interval` (ou 120 sec), et modifie l'élément en fonction de `tpl-type` si
l'expression `tpl-if` est vraie.

### API

 - `tpl-if` : *Expression javascript*. Permet de définir si l'élément doit être créé (peut-être le nom d'une propriété booléenne)
 - `tpl-interval` : *Nombre*. Le delai d'actualisation (par défaut 120)
 - `tpl-request` : *Chaine de caractère*. Url de l'api
 - `tpl-type` : Valeur: child
 - `tpl-next` : Lit le suivant

### Attributs modificateurs

 - `tpl-content` et `tpl-content-filter`
 - `tpl-attr-{name}` et `tpl-attr-{name}-filter`

### Les expressions javascript

Certain attribut comme `tpl-if` supporte les expressions javascript. Ils vont eval leur contenu par exemple `tpl-if="is_read"`
va être traduit en : `return is_read` avec la scope: `results[n]` c'est-à-dire que `is_read` sera compris comme l'expression
`results[n].is_read`.

## Type child

Ajoute un élément enfant si l'expression `tpl-if` est vraie. Si l'attribut `tpl-uniqid` est défini sur l'**élément enfant direct**, l'id devra être unique sinon le contenu de l'élément sera
remplacé.

*/

(function() {
  const formatters = {
    format_date: (dateString, args) => {
      const date = new Date(dateString)
      return date.toLocaleDateString().replace(/2\d(\d{2})/, '$1') + ' à ' + date.toLocaleTimeString().replace(/\:(\d+):\d+$/, 'h$1')
    },
    capfirst: (str) => str.charAt(0).toUpperCase() + str.slice(1)
  }

  function apply_filters(str, filter) {
    if (!filter) {
      return str
    }
    const filters = filter.split('|')

    filters.forEach((key) => {
      const split = key.split(':')
      const name = split[0].toLowerCase()
      try {
        if (formatters[name]) {
          str = formatters[name].call(this, str, split[1]) // @TODO: Improve args
        }
      } catch (e) {
        console.warn(e, split)
        return false;
      }
    })

    return str
  }

  function eval_scope(str, scope) {
    try {
      with (scope) {
        return eval(str)
      }
    } catch (e) {
      console.warn(e, scope)
      return false;
    }
  }

  function get(str, scope) {
    try {
      const arr = str.split('.') // @TODO: Add `https://www.npmjs.com/package/objectpath`
      let sibling = scope
      while (arr.length) {
        sibling = sibling[arr.shift(0)]
      }
      return sibling
    } catch (e) {
      console.warn(e, scope)
      return "";
    }
  }

  function clone(template, scope) {
    const item = template.content.cloneNode(true).children[0]

    const uniqid = get(item.getAttribute('tpl-uniqid'), scope) // @TODO: Uniqid seulement si l'attribut est défini dans le template

    const domElement = $(template.parentNode).find(`> *[data-uniqid=${uniqid}]`)[0]
    if (domElement) {
      return domElement.removeAttribute('tpl-old')
    }

    item.setAttribute('data-uniqid', uniqid)
    item.removeAttribute('tpl-uniqid')

    item.querySelectorAll('*').forEach(function (element) {
      const attributes = element.attributes
      for (let i = attributes.length - 1; i >= 0; i--) {
        const attr = attributes[i]
        const attrFilter = (attributes[attr.name + '-filter'] && attributes[attr.name + '-filter'].value)
        if (attr.name === 'tpl-content') {
          element.textContent = apply_filters(get(element.getAttribute('tpl-content'), scope), attrFilter)

          element.removeAttribute(attr.name)
          attrFilter && element.removeAttribute(attr.name + '-filter')
          continue
        }

        const match = attr.name.match(/^tpl-attr-(\w+)$/i)
        if (match) {
          element.setAttribute(match[1], apply_filters(get(attr.value, scope), attrFilter))
          
          element.removeAttribute(attr.name)
          attrFilter && element.removeAttribute(attr.name + '-filter')
          continue
        }
      }
    })

    //template.parentElement.appendChild(item)
    template.parentElement.insertBefore(item, template.parentElement.children[0]);
  }

  function fetch(template, next) {
    jQuery.ajax({
      url: next || template.getAttribute('tpl-request'),
      method: 'GET',
      data: {
        'anti-cache': (+new Date())
      },
      dataType: 'json',
      success: (json) => {
        // @TODO: Don't remove, replace with uniqid

        if (!next) {
          const children = template.parentElement.children
          for (let i = children.length - 1; i >= 0; i--) {
            if (children[i].tagName !== "TEMPLATE")
              children[i].setAttribute('tpl-old', 'old')
          }
        }

        const tplIf = template.getAttribute('tpl-if')
        json.results.forEach(function (scope) {
          if (eval_scope(tplIf, scope)) {
            clone(template, scope)
          }
        })

        if (json.next && template.hasAttribute('tpl-next')) {
          return fetch(template, json.next)
        } else {
          const children = template.parentElement.children
          for (let i = children.length - 1; i >= 0; i--) {
            if (children[i].hasAttribute('tpl-old'))
              children[i].remove()
          }
        }

        var event = new Event('template-changed');
        template.dispatchEvent(event);
      }
    })
  }

  document.querySelectorAll('template[tpl-request]').forEach(function (template) {
    if (template.getAttribute('tpl-type') != 'child')
      throw new Error('Unsupported type', template)

    // UNCOMMENT FOR DEV ONLY :
    // fetch(template)

    const sec = +template.getAttribute('tpl-interval') * 1000 || 120000
    // @TODO: Décaler dans le temps les appels à l'API:
    setInterval(fetch, (sec > 10000) ? sec : 10000, template)
  })
})()
