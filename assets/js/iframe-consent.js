(function() {
  // Part of this script is hard-coded into the HTML code for performance reasons.
  // It can be found at the bottom of template/base.html

  for (const placeholder of document.querySelectorAll('.iframe-placeholder')) {
    const message = document.createElement('p')
    message.innerHTML = "Attention, ce contenu provient d'une source externe !"
    const button = document.createElement('button')
    button.innerHTML = 'Charger le contenu'
    button.addEventListener('click', function(e) {
      const placeholder = e.target.parentElement
      const index = placeholder.dataset.iframeIndex
      placeholder.outerHTML = window.iframeStash[index]
    })

    placeholder.appendChild(message)
    placeholder.appendChild(button)
  }
})()
