// to handle a new type of answer, you just need to create a method called
// initializeXXX(answers) that will add the reset the field content and mark good answer
// then add the two methods in the callback lists

let index = 0
function extractAnswer(radio, answers) {
  radio.forEach((rb) => {
    if (!rb.parentElement.parentElement.getAttribute('id')) {
      rb.parentElement.parentElement.setAttribute('id', 'id-' + (index++))
    }
    rb.setAttribute('name', rb.parentElement.parentElement.getAttribute('id'))
    if (!answers[rb.parentNode.parentNode.getAttribute('id')]) {
      answers[rb.parentNode.parentNode.getAttribute('id')] = [rb.checked]
    } else {
      answers[rb.parentNode.parentNode.getAttribute('id')].push(rb.checked)
    }
    rb.setAttribute('value', answers[rb.parentNode.parentNode.getAttribute('id')].length - 1)
    rb.disabled = false
    rb.checked = false
  })
}
function initializeCheckboxes(answers) {
  const checkboxes = document.querySelectorAll('.quizz ul li input[type=checkbox]')
  extractAnswer(checkboxes, answers)
}



function initializeRadio(answers) {
  const radio = document.querySelectorAll('.quizz ul li input[type=radio]')
  extractAnswer(radio, answers)
}

const initializePipeline = [initializeCheckboxes, initializeRadio]
function computeForm(formdata, answers) {
  const badAnswers = []
  formdata.entries().forEach(entry => {
    const name = entry[0]
    const values = entry[1]
    let good = true
    if (!answers[name]) {
      console.log('not found ' + name)
      return 0
    } else {
      // for poc we assume we only deal with lists
      for (let i = 0; i < answers[name].length && good; i++) {
        if (answers[name][i]) {
          good = good && values.indexOf(answers[name][i]) !== -1
        } else {
          good = good && values.indexOf(answers[name][i]) === -1
        }
        if (!good) {
          badAnswers.push(name)
        }
      }
    }
  })
}
function markBadAnswers(names, answers) {
  names.forEach(name => {
    document.querySelectorAll('input[name=' + name + ']').forEach(field => {
      if (answers[name].indexOf(field.getAttribute('value')) !== -1 && !field.checked) {
        field.addClass('quizz-forget')
      } else if (answers[name].indexOf(field.getAttribute('value')) === -1 && field.checked) {
        field.addClass('quizz-bad')
      }
    })
  })
}
const answers = {}
initializePipeline.forEach(func => func(answers))
document.querySelectorAll('form.quizz').forEach(form => {
  form.addEventListener('submit', e => {
    e.preventDefault()
    e.stopPropagation()
    const formData = new FormData(form)
    // result = name of bad answers
    const result = computeForm(formData, answers)
    markBadAnswers(result, answers)
    // here send result
    console.log(result)
  })
})
