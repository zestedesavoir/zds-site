(function() {
  const banner = document.getElementById('very-top-banner')
  if (!banner) {
    return
  }
  const slug = banner.dataset.slug

  if (localStorage.getItem('hide-very-top-banner') === slug || sessionStorage.getItem('hide-very-top-banner') === slug) {
    banner.remove()
    document.body.classList.remove('has-top-banner')
  } else {
    document.body.classList.add('has-top-banner')

    document.querySelector('#very-top-banner button').addEventListener('click', e => {
      banner.remove()
      document.body.classList.remove('has-top-banner')

      sessionStorage.setItem('hide-very-top-banner', slug)
      if (e.shiftKey || e.ctrlKey) {
        localStorage.setItem('hide-very-top-banner', slug)
      }
    })
  }
}())
