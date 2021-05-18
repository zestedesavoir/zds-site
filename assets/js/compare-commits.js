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
        r => Array.prototype.forEach.call(r.querySelectorAll('[name="compare-to"]'), elem => elem.removeAttribute('disabled'))
      )
      nextAll(row).forEach(
        r => Array.prototype.forEach.call(r.querySelectorAll('[name="compare-to"]'), elem => elem.setAttribute('disabled', true))
      )
      Array.prototype.forEach.call(row.querySelectorAll('[name="compare-to"]'), elem => elem.setAttribute('disabled', true))
    } else {
      prevAll(row).forEach(
        r => Array.prototype.forEach.call(r.querySelectorAll('[name="compare-from"]'), elem => elem.setAttribute('disabled', true))
      )
      nextAll(row).forEach(
        r => Array.prototype.forEach.call(r.querySelectorAll('[name="compare-from"]'), elem => elem.removeAttribute('disabled'))
      )
      Array.prototype.forEach.call(row.querySelectorAll('[name="compare-from"]'), elem => elem.setAttribute('disabled', true))
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    Array.prototype.forEach.call(document.querySelectorAll('.commits-list input[name^="compare"]:checked'), elem => toogleRadioInput(elem))
    Array.prototype.forEach.call(document.querySelectorAll('.commits-list input[name^="compare"]'), elem =>
      elem.addEventListener('change', function() {
        toogleRadioInput(this)
      })
    )
    Array.prototype.forEach.call(document.querySelectorAll('.commits-compare-form'), elem =>
      elem.addEventListener('submit', function(e) {
        const compareFrom = document.querySelector(".commits-list input[name='compare-from']:checked").value
        const compareTo = document.querySelector(".commits-list input[name='compare-to']:checked").value

        this.querySelector("input[name='from']").value = compareFrom
        this.querySelector("input[name='to']").value = compareTo
      })
    )
  })
})()
