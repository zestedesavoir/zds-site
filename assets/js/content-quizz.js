// to handle a new type of answer, you just need to create a method called
// initializeXXX(answers) that will add the reset the field content and mark good answer
// then add the two methods in the callback lists

let index = 0

function extractAnswer(inputDomElementList, answers) {
  inputDomElementList.forEach((rb) => {

    let ulWrapperElement = rb.parentElement.parentElement;
    // we give the ui an id to find the element in a more effective way later when the users answer the questions
    if (!ulWrapperElement.getAttribute('id')) {
      ulWrapperElement.setAttribute('id', 'id-' + (index++))
    }
    rb.setAttribute('name', ulWrapperElement.getAttribute('id'))
    let questionBlock = ulWrapperElement.parentElement.parentElement;
    questionBlock.setAttribute('data-name', rb.getAttribute('name'))
    if (!answers[ulWrapperElement.getAttribute('id')]) {
      answers[ulWrapperElement.getAttribute('id')] = [rb.checked]
    } else {
      answers[ulWrapperElement.getAttribute('id')].push(rb.checked)
    }
    rb.setAttribute('value', answers[ulWrapperElement.getAttribute('id')].length - 1)
    rb.disabled = false
    rb.checked = false
  })
}

/**
 * The full quizz is contained in a div or article that has class "quizz".
 * Then one question is inside a zmarkdown "custom-block" of type "custom-block-quizz". Two possibilities :
 *
 * Without explanation for correction :
 *
 * <code>
 *   <div class="custom-block custom-block-quizz">
 *     <div class="custom-block-heading">The question</div>
 *     <div class="custom-block-body">
 *       <ul><li><input type="checkbox" value="the answer"/>the answer</li>
 *       <li><input type="checkbox" value="the good answer" checked/>the good answer</li>
 *       </ul>
 *     </div>
 *   </div>
 * </code>
 *
 * With an explanation inside another custom block most of time a custom-block-neutral
 *
 * <code>
 *   <div class="custom-block custom-block-quizz">
 *     <div class="custom-block-heading">The question</div>
 *     <div class="custom-block-body">
 *       <ul><li><input type="checkbox" value="the answer"/>the answer</li>
 *       <li><input type="checkbox" value="the good answer" checked/>the good answer
 *           <div class="custom-block custom-block-neutral">
 *         <div class="custom-block-heading">Explanation</div>
 *         <div class="custom-block-body">a formatted text</div>
 *       </div></li>
 *       </ul>

 *     </div>
 *   </div>
 * </code>
 *
 * Note that the correction MAY be inside the last li due to the way custom-block plugin works, this is not a bug
 *
 * @param answers the answer dictionary, it will be modified by the process
 */
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
  const allAnswerNames = []
  for (const entry of formdata.entries()) {
    const name = entry[0]
    const values = parseInt(entry[1], 10)
    allAnswerNames.push(name)
    if (!answers[name]) {
      continue
    } else {
      // for poc we assume we only deal with lists
      if (!answers[name][values]) {
        badAnswers.push({
          name: name,
          value: values
        })
      }
    }
  }
  return [badAnswers, allAnswerNames]
}

function markBadAnswers(names, answers) {
  const toAdd = []
  if (names.length === 0) {
    Object.keys(answers).forEach(answer => {
      let mustMarkBad = false
      answers[answer].forEach((value, index) => {
        const inputAnswer = document.querySelector(`#${answer} input[value="${index}"]`)
        if (value && !inputAnswer.checked) {
          inputAnswer.parentElement.classList.add('quizz-forget')
          mustMarkBad = true
        }
      })
      if (mustMarkBad) {
        document.querySelector(`div[data-name="${answer}"]`).classList.add('quizz-bad')
      }
    })
  }
  names.forEach(({ name }) => {
    document.querySelectorAll('input[name="' + name + '"]').forEach(field => {
      if (answers[name][parseInt(field.getAttribute('value'), 10)] && !field.checked) {
        field.parentElement.classList.add('quizz-forget')
        toAdd.push({
          name: name,
          value: field.getAttribute('value')
        })
      }
    })
    document.querySelector(`.custom-block[data-name=${name}]`).classList.add('quizz-bad')
  })
  names.forEach(({
    name,
    value
  }) => {
    document.querySelector(`input[type=checkbox][name="${name}"][value="${value}"]`)
      .parentElement.classList.add('quizz-bad')
  })
  toAdd.forEach(name => names.push(name))
}

function getWantedHeading(questionNode, nodeName, attr) {
  let potentialHeading = questionNode
  while (potentialHeading[attr] &&
  potentialHeading.nodeName !== nodeName.toUpperCase()) {
    potentialHeading = potentialHeading[attr]
  }
  if (potentialHeading.nodeName !== nodeName.toUpperCase()) {
    return null
  }
  return potentialHeading
}

/**
 * As we are using forms to capture the answer and send the result back to user (and flushing stats for authors),
 * we need to add an html form.
 *
 * The main issue is that it was asked to have many quizz inside a tutorial section, not just a list of questions in a
 * specific section. As a result we had to find an heuristic :
 * - if the current section has no h3 headings, we just span the form from the beggining to the end of section
 * - if the current section has one or more h3 headings, we start the form just after it and end it at just before the
 * next h3 heading if there is one or the end of form
 *
 * @param quizz current quizz container
 * @param answers answers dictionary
 */
function injectForms(quizz, answers) {
  const searchedTitle = quizz.getAttribute('data-heading-level') || 'h3'
  const submitLabel = quizz.getAttribute('data-quizz-validate') || 'Validate'
  const headings = {}
  let idBias = 0
  const wrappers = []
  Object.keys(answers).forEach(blockId => {
    const blockNode = document.getElementById(blockId)
    if (!blockNode) {
      // if the node was treated and  therefore the clone has not been reinserted yet
      return
    }
    // this is the custom-block-quizz node
    const questionNode = blockNode.parentElement.parentElement
    const heading = getWantedHeading(questionNode, searchedTitle, 'previousSibling') || quizz
    if (!heading.getAttribute('id')) {
      heading.setAttribute('id', `quizz-form-${idBias}`)
      idBias++
    }
    if (heading && !headings[heading.getAttribute('id')]) {
      // this is just for convenience, this add a "known" element that will always be there
      const wrapper = document.createElement('div')

      headings[heading.getAttribute('id')] = true
      const form = document.createElement('form')
      form.classList.add('quizz')

      const submit = document.createElement('button')
      submit.innerText = submitLabel
      submit.classList.add('btn', 'btn-submit')
      const result = document.createElement('p')
      result.classList.add('result')
      let nodeToAddToForm
      if (heading === quizz) {
        nodeToAddToForm = quizz.firstChild
      } else {
        nodeToAddToForm = heading.nextSibling
      }
      form.method = 'POST'
      form.setAttribute('action', quizz.getAttribute('data-answer-url'))
      // gather all the questions of this current subsection, until the next h3 heading
      while (nodeToAddToForm && nodeToAddToForm.nodeName !== searchedTitle.toUpperCase()) {
        const current = nodeToAddToForm
        nodeToAddToForm = nodeToAddToForm.nextSibling
        form.appendChild(current.cloneNode(true))
        current.parentNode.removeChild(current)
      }
      form.appendChild(result)
      form.appendChild(submit)
      wrappers.push(wrapper)
      if (nodeToAddToForm && nodeToAddToForm.nodeName === searchedTitle.toUpperCase()) {
        wrapper.append(form)
        wrappers.push(nodeToAddToForm.cloneNode(true))
      } else {
        wrapper.appendChild(form)
        if (heading.nextSibling) {
          wrapper.appendChild(heading.nextSibling.cloneNode(true))
          heading.parentNode.removeChild(heading.nextSibling)
        }
      }
    }
    // avoid doubly
    if (heading.nodeName === searchedTitle.toUpperCase()) {
      quizz.removeChild(heading)
    }
  })
  wrappers.forEach((wrapper) => quizz.appendChild(wrapper))
}

const answers = {}
initializePipeline.forEach(func => func(answers))
document.querySelectorAll('div.quizz').forEach(div => {
  injectForms(div, answers)
})

function sendQuizzStatistics(form, statistics) {
  const csrfmiddlewaretoken = document.querySelector('input[name=\'csrfmiddlewaretoken\']').value
  const xhttp = new XMLHttpRequest()
  xhttp.open('POST', form.getAttribute('action'))
  xhttp.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
  xhttp.setRequestHeader('Content-Type', 'application/json')
  xhttp.setRequestHeader('X-CSRFToken', csrfmiddlewaretoken)
  statistics.url = form.parentElement.parentElement.previousElementSibling.firstElementChild.href
  xhttp.send(JSON.stringify(statistics))
}

function displayResultAfterSubmitButton(nbGood, nbTotal, form) {
  const percentOfAnswers = (100 * 1.0 * nbGood / nbTotal).toLocaleString('fr-FR', {
    minimumIntegerDigits: 1,
    useGrouping: false
  })
  form.querySelector('.result').innerText = `Vous avez bien répondu à ${percentOfAnswers}% des questions.`
}

document.querySelectorAll('form.quizz').forEach(form => {
  // compute the answer and send stats
  form.addEventListener('submit', e => {
    e.preventDefault()
    e.stopPropagation()
    const formData = new FormData(form)
    // result = name of bad answers
    const [badAnswerNames, allAnswerNames] = computeForm(formData, answers)
    markBadAnswers(badAnswerNames, answers)
    allAnswerNames.forEach(name => {
      const ulWrapper = document.getElementById(name);
      const quizzCustomBlock = ulWrapper.parentElement.parentElement;
      quizzCustomBlock.classList.add('hasAnswer')
    })
    const questions = []
    badAnswerNames.forEach(result => {
      if (questions.indexOf(result.name) === -1) {
        questions.push(result.name)
      }
    })
    const statistics = {
      expected: {},
      result: {}
    }
    let nbGood = 0
    let nbTotal = 0
    Object.keys(answers).forEach(name => {
      const element = document.querySelector(`.custom-block[data-name="${name}"]`)
      let title = element.querySelector('.custom-block-heading').textContent
      const correction = element.querySelector('.custom-block-body .custom-block')
      if (correction && title.indexOf(correction.textContent) > 0) {
        title = title.substr(0, title.indexOf(correction.textContent))
      }
      statistics.result[title] = {
        evaluation: 'bad',
        labels: []
      }
      statistics.expected[title] = {}
      const availableResponses = element.querySelectorAll('input')
      for (let i = 0; i < availableResponses.length; i++) {
        // wee need to get the question label for statistics
        const liWrapper = availableResponses[i].parentElement;
        let questionLabel = liWrapper.textContent
        if (correction && questionLabel.indexOf(correction.textContent) !== -1) {
          questionLabel = questionLabel.substring(0, questionLabel.indexOf(correction.textContent))
        }
        statistics.expected[title][questionLabel] = answers[name][i]
      }
      // now determine answers and their labels
      element.querySelectorAll('input:checked')
        .forEach(node => {
          // remove eventual glued corretion
          let label = node.parentElement.textContent
          if (correction && label.indexOf(correction.textContent) !== -1) {
            label = label.substr(0, label.indexOf(correction.textContent))
          }
          statistics.result[title].labels.push(label.trim())
        })
      if (element.classList.contains('hasAnswer')) {
        nbTotal++

        if (!element.classList.contains('quizz-bad') &&
          !element.classList.contains('quizz-forget')) {
          element.classList.add('quizz-good')
          statistics.result[title].evaluation = 'ok'
          nbGood++
        }
      }
    })
    sendQuizzStatistics(form, statistics);
    displayResultAfterSubmitButton(nbGood, nbTotal, form);
  })
})
