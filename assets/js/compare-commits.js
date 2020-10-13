/*
 * Allow the user to compare two commits
 */

(function() {
  function prevAll(element) {
    const result = []
    while (element) {
      result.push(element)
      element = element.previousElementSibling
    }
    return result
  }

  function nextAll(element) {
    const result = []
    while (element) {
      result.push(element)
      element = element.nextElementSibling
    }
    return result
  }

  function toogleRadioInput(radioInput) {
    const row = radioInput.parentNode.parentNode

    if (radioInput.getAttribute('name') === 'compare-from') {
      prevAll(row).forEach(
        r => Array.from(r.querySelectorAll('[name="compare-to"]')).forEach(item => item.removeAttribute('disabled'))
      )
      nextAll(row).forEach(
        r => Array.from(r.querySelectorAll('[name="compare-to"]')).forEach(item => item.setAttribute('disabled', true))
      )
      Array.from(row.querySelectorAll('[name="compare-to"]')).forEach(item => item.setAttribute('disabled', true))
    } else {
      prevAll(row).forEach(
        r => Array.from(r.querySelectorAll('[name="compare-from"]')).forEach(item => item.setAttribute('disabled', true))
      )
      nextAll(row).forEach(
        r => Array.from(r.querySelectorAll('[name="compare-from"]')).forEach(item => item.removeAttribute('disabled'))
      )
      Array.from(row.querySelectorAll('[name="compare-from"]')).forEach(item => item.setAttribute('disabled', true))
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    Array.from(document.querySelectorAll('.commits-list input[name^="compare"]:checked')).forEach(radioElement => toogleRadioInput(radioElement))

    Array.from(document.querySelectorAll('.commits-list input[name^="compare"]')).forEach((el) => {
      el.addEventListener('change', function() {
        toogleRadioInput(this)
      })
    })

    Array.from(document.querySelectorAll('.commits-compare-form')).forEach((el) => {
      el.addEventListener('submit', function(e) {
        const fromInput = this.querySelector("input[name='from']")
        const toInput = this.querySelector("input[name='to']")
        const compareFrom = document.querySelector(".commits-list input[name='compare-from']:checked").value
        const compareTo = document.querySelector(".commits-list input[name='compare-to']:checked").value

        fromInput.value = compareFrom
        toInput.value = compareTo
      })
    })
  })
})()
