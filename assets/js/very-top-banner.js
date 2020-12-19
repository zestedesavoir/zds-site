(function() {
  const banner = document.getElementById('very-top-banner')
  if (!banner) {
    return
  }

  const slug = banner.dataset.slug

  /**
   * Removes the banner if the local storage says so.
   * Returns `true` if a banner vas removed.
   */
  function removeBannerIfNeeded() {
    if (localStorage.getItem('hide-very-top-banner') === slug || sessionStorage.getItem('hide-very-top-banner') === slug) {
      banner.remove()
      document.body.classList.remove('has-top-banner')
      return true
    } else {
      return false
    }
  }

  if (!removeBannerIfNeeded()) {
    document.body.classList.add('has-top-banner')

    banner.querySelector('button').addEventListener('click', e => {
      banner.remove()
      document.body.classList.remove('has-top-banner')

      sessionStorage.setItem('hide-very-top-banner', slug)
      if (e.shiftKey || e.ctrlKey) {
        localStorage.setItem('hide-very-top-banner', slug)
      }
    })

    // Runs when the local storage is modified from another tab. So the banner
    // will be removed from all tabs at once if removed permanently using ctrl
    // or shift, but not in other cases as it's then stored on the session
    // storage.
    window.addEventListener('storage', removeBannerIfNeeded)
  }
}())
