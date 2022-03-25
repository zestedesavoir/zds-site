/* ===== Zeste de Savoir ====================================================
   Preview when editing news
   ========================================================================== */

(function($) {
  function convertToNbsp(text) {
    // Any change here should also be made in zds/utils/templatetags/french_typography.py
    return text
      .replace(' ;', '&#8239;;')
      .replace(' ?', '&#8239;?')
      .replace(' !', '&#8239;!')
      .replace(' %', '&#8239;%')
      .replace('« ', '«&nbsp;')
      .replace(' »', '&nbsp;»')
      .replace(' :', '&nbsp;:')
  }

  function updatePreview(data, element) {
    const $el = $(element)
    if (data.image) {
      $el.find('.featured-resource-illu').show().attr('src', data.image)
    } else {
      $el.find('.featured-resource-illu').hide()
    }

    $el.find('h2').html(data.title)
    $el.find('.featured-resource-description').html(data.description)
    $el.find('a').attr('href', data.link)
  }

  function buildDescription(authors, type) {
    let text = type
    if (authors.length > 0) { text += ' par ' + authors }
    return text
  }

  $('.featured-resource-edit-form form input').on('change input', function() {
    updatePreview({
      image: $('.featured-resource-edit-form input[name=image_url]').val(),
      title: convertToNbsp($('.featured-resource-edit-form input[name=title]').val()),
      description: buildDescription(
        $('.featured-resource-edit-form input[name=authors]').val(),
        convertToNbsp($('.featured-resource-edit-form input[name=type]').val())
      ),
      link: $('.featured-edit-form input[name=url]').val()
    }, $('.featured-resource-edit-form .featured-resource-item'))
  })
})(jQuery)
