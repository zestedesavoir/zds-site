
(function($) {
  'use strict'
  const shareModal = $('#share-to-mastodon')
  const shareButton = shareModal.find('button')

  shareModal.find("input[name='instance']").on('change paste keyup', function() {
    // start by chars (https://)
    if (this.value.startsWith('https://')) {
      shareButton.prop('disabled', false)
    } else {
      shareButton.prop('disabled', true)
    }
  })

  shareModal.on('submit', function() {
    shareModal.attr('action', shareModal.find("input[name='instance']").val() + '/share')
  })
})(jQuery)
