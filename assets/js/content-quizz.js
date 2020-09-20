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
  for (const entry of formdata.entries()) {
    const name = entry[0]
    const values = parseInt(entry[1], 10)
    if (!answers[name]) {
      console.log('not found ' + name)
      continue
    } else {
      console.log(name + ' ' + values + ' : ' + answers[name][values])
      // for poc we assume we only deal with lists
      if (!answers[name][values]) {
        console.log('bad answer ' + name + ' ' + values)
        badAnswers.push({
          name: name,
          value: values
        })
      }
    }
  }
  return badAnswers
}

function markBadAnswers(names, answers) {
  console.log(names)
  console.log(answers)
  Object.keys(names).forEach(name => {
    console.log(names)
    document.querySelectorAll('input[name="' + name + '"]').forEach(field => {
      if (answers[name][parseInt(field.getAttribute('value'), 10)] && !field.checked) {
        field.parentElement.classList.add('quizz-forget')
      }
    })
  })
  names.forEach(({ name, value }) => {
    console.log('name ' + name)
    console.log('value ' + value)
    document.querySelector(`input[type=checkbox][name="${name}"][value="${value}"]`).classList.add('quizz-forget')
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
