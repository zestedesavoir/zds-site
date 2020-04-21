/*
 * Allow the user to compare two commits
 */

(function($) {
  'use strict'

  function toogleRadioInput($radioInput) {
    var $row = $radioInput.parent().parent()

    if ($radioInput.attr('name') === 'compare-from') {
      $row.prevAll().find("[name='compare-to']").prop('disabled', false)
      $row.nextAll().find("[name='compare-to']").prop('disabled', true)
      $row.find("[name='compare-to']").prop('disabled', true)
    } else {
      $row.prevAll().find("[name='compare-from']").prop('disabled', true)
      $row.nextAll().find("[name='compare-from']").prop('disabled', false)
      $row.find("[name='compare-from']").prop('disabled', true)
    }
  }

  $(".commits-list input[name^='compare']").on('change', function() {
    toogleRadioInput($(this))
  })

  $(document).ready(function() {
    $(".commits-list input[name^='compare']:checked").each(function() {
      toogleRadioInput($(this))
    })
  })

  $('.commits-compare-form').on('submit', function() {
    var $form = $(this)
    var $fromInput = $form.find("input[name='from']")
    var $toInput = $form.find("input[name='to']")
    var compareFrom = $(".commits-list input[name='compare-from']:checked").val()
    var compareTo = $(".commits-list input[name='compare-to']:checked").val()

    $fromInput.val(compareFrom)
    $toInput.val(compareTo)
  })
})(jQuery)
