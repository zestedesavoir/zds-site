// to handle a new type of answer, you just need to create a method called
// initializeXXX(answers) that will add the reset the field content and mark good answer
// then add the two methods in the callback lists

let index = 0

function extractAnswer(inputDomElementList, answers) {
  
  inputDomElementList.forEach((rb) => {

    const ulWrapperElement = rb.parentElement.parentElement
    // we give the ui an id to find the element in a more effective way later when the users answer the questions
    if (!ulWrapperElement.getAttribute('id')) {
      ulWrapperElement.setAttribute('id', 'id-' + (index++))
    }

    rb.setAttribute('name', ulWrapperElement.getAttribute('id'))

    const questionBlock = ulWrapperElement.parentElement.parentElement
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
 * 
 *           <div class="custom-block custom-block-neutral">
 *         <div class="custom-block-heading">Explanation</div>       
 *         <div class="custom-block-body">a formatted text</div>
 *       </div></li>
 * 
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

  // add explanation to all questions
  document.querySelectorAll('div.quizz').forEach(quizz => {
    const quizzDivs = quizz.querySelectorAll('div.custom-block-quizz');
    quizzDivs.forEach(quizzDiv => {
      const ul = quizzDiv.querySelector('ul')
      const lastLi = ul.lastElementChild
      const explanationText = '<b>Explication :</b>' + lastLi.innerText
      const explanation = document.createElement('div')
      explanation.classList.add('explanation_off')
      explanation.innerHTML = explanationText
      lastLi.parentNode.removeChild(lastLi);
      quizzDiv.querySelector('div.custom-block-body').appendChild(explanation)

    });
  })


  const checkboxes = document.querySelectorAll('.quizz ul li input[type=checkbox]')
  extractAnswer(checkboxes, answers)

}

function initializeRadio(answers) {
  const radio = document.querySelectorAll('.quizz ul li input[type=radio]')
  extractAnswer(radio, answers)
}

const initializePipeline = [initializeCheckboxes]

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

function markBadAnswers(form, names, answers) {

  const toAdd = []

  Object.keys(answers).forEach(answer => {

    const inputs = form.querySelectorAll(`#${answer} input`);


    let numChecked = 0;
    inputs.forEach(input => {
      if (input.hasAttribute('checked')) {
        input.parentElement.classList.add('answer-good')
        numChecked++;
      }
    });

    // question with more than one correct answer
    if (numChecked > 1) {

      let AnsweredWell = true
      answers[answer].forEach((value, index) => {
        const inputAnswer = document.querySelector(`#${answer} input[value="${index}"]`)
        if (value && !inputAnswer.checked) {
          AnsweredWell = false
        }
      })

      const divquizz = form.querySelector(`div[data-name="${answer}"]`)
      if (!AnsweredWell) {
        divquizz.classList.add('quizz-bad')
      } else {
        divquizz.classList.add('quizz-good')
      }
    }
  })

  names.forEach(({ name }) => {

    form.querySelectorAll('input[name="' + name + '"]').forEach(field => {


      if (answers[name][parseInt(field.getAttribute('value'), 10)] && !field.checked) {

        toAdd.push({
          name: name,
          value: field.getAttribute('value')
        })
      }
    })

    const divquizz = form.querySelector(`.custom-block[data-name=${name}]`)
    if (!divquizz.classList.contains('quizz-good')) divquizz.classList.add('quizz-bad');
  })

  names.forEach(({
    name,
    value
  }) => {

    form.querySelector(`input[type=checkbox][name="${name}"][value="${value}"]`).parentElement.classList.add('answer-bad')
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


function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
  });
}

/**

 */
function injectForms(quizz, answers) {


  const searchedTitle = quizz.getAttribute('data-heading-level') || 'h3'
  const submitLabel = quizz.getAttribute('data-quizz-validate') || 'Validate'
  const headings = {}
  const wrappers = []


  const QuizzQstNum = quizz.querySelectorAll('.custom-block-quizz').length

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
      submit.style.marginTop = '-22px'

      submit.classList.add('btn', 'btn-submit')
      
      submit.setAttribute('id', `my-button-${idButton}`);
      idButton++

      const notAnswered = document.createElement('p')
      notAnswered.classList.add('notAnswered')

      let nodeToAddToForm
      if (heading === quizz) {

        nodeToAddToForm = quizz.firstChild
      } else {
        nodeToAddToForm = heading.nextSibling
      }


      // add any element before  the first question to the wrapper
      while (nodeToAddToForm.nodeName !== "DIV" && nodeToAddToForm.className !== "custom-block custom-block-quizz"){

        const current = nodeToAddToForm
        nodeToAddToForm = nodeToAddToForm.nextSibling
        wrapper.appendChild(current.cloneNode(true))
        current.parentNode.removeChild(current)

      }
  
      form.method = 'POST'
      form.setAttribute('action', quizz.getAttribute('data-answer-url'))
      form.setAttribute('id', `my-form-${idCounter}`);
      idCounter++;


      // add elements between 1st and last question to form
      let num = 0;
      while (nodeToAddToForm && nodeToAddToForm.nodeName !== searchedTitle.toUpperCase()) {
        const current = nodeToAddToForm
        if ( current.nodeName === "DIV" && current.className === "custom-block custom-block-quizz") num++;
        nodeToAddToForm = nodeToAddToForm.nextSibling
        form.appendChild(current.cloneNode(true))
        current.parentNode.removeChild(current)
        if ( num === QuizzQstNum )  {form.appendChild(submit) ; break};
      }
      wrapper.append(form)

      // add elements after last question until next h3 to wrapper
      while (nodeToAddToForm && nodeToAddToForm.nodeName !== searchedTitle.toUpperCase()) {

        const current = nodeToAddToForm
        nodeToAddToForm = nodeToAddToForm.nextSibling
        wrapper.appendChild(current.cloneNode(true))
        current.parentNode.removeChild(current)
      }

      wrapper.appendChild(notAnswered)
      wrappers.push(wrapper)
      
    }
    // avoid doubly
    if (heading.nodeName === searchedTitle.toUpperCase()) {
      quizz.removeChild(heading)
    }
  })
  wrappers.forEach((wrapper) => quizz.appendChild(wrapper))
}

let answers = {}

initializePipeline.forEach(func => func(answers))

let idCounter = 0
let idBias = 0


let idButton =  0;

// parseInt(sessionStorage.getItem('idButton')) ||

document.querySelectorAll('div.quizz').forEach(div => {

  const quizInside = div.querySelector('.custom-block-quizz ul li input[type=checkbox]');
  if (quizInside) {
    injectForms(div, answers)
  }

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

function displayResultAfterSubmitButton(form) {

  const questions = form.querySelectorAll('.custom-block-quizz');

  for (let question of questions) {

    const explanationElement = question.querySelector('.explanation_off')
    if (explanationElement !== null) {
      explanationElement.classList.remove('explanation_off');
      explanationElement.classList.add('explanation_on');
    }

  }

}

// test if the quizz is totally answered or not
function QuizzAnswered(form) {

  const questions = form.querySelectorAll('.custom-block-quizz');
  for (let question of questions) {
    const checkboxes = question.querySelectorAll('input[type="checkbox"]');
    let isQuestionValid = false;
    for (let checkbox of checkboxes) {
      if (checkbox.checked) {
        isQuestionValid = true;
        break;
      }
    }
    if (!isQuestionValid) {
      return false
    }
  }
  return true
}



document.querySelectorAll('form.quizz').forEach(form => {

  form.addEventListener('submit', e => {

    e.preventDefault()
    e.stopPropagation()

    const notAnswered = form.parentElement.querySelector('.notAnswered');
    const submitBtn = form.querySelector('.btn-submit');


    if (!document.querySelector('input[name=\'csrfmiddlewaretoken\']')) {
      if (!sessionStorage.getItem(submitBtn.id)) {
        // If the quiz has not been submitted before, store a flag in session storage to prevent multiple submissions
        sessionStorage.setItem(`${submitBtn.id}`, true);
      } else {
        // If the quiz has already been submitted, disable the submit button
        submitBtn.setAttribute('disabled', true);
        alert('Vous avez deja repondu, Veuillez se connecter');
        return;
      }
    }

    // test if the whole quizz is answered
    if (QuizzAnswered(form)) {

      const formData = new FormData(form)
      const [badAnswerNames, allAnswerNames] = computeForm(formData, answers)

      markBadAnswers(form, badAnswerNames, answers)

      allAnswerNames.forEach(name => {
        const ulWrapper = document.getElementById(name)
        const quizzCustomBlock = ulWrapper.parentElement.parentElement
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

        //make statistics of concerned form only

        const CurrentFormQuestions = [...form.querySelectorAll('.custom-block-heading')].map(question => question.textContent);

        if (CurrentFormQuestions.includes(title)) {

          const availableResponses = element.querySelectorAll('input')
          for (let i = 0; i < availableResponses.length; i++) {
            // wee need to get the question label for statistics
            const liWrapper = availableResponses[i].parentElement
            let questionLabel = liWrapper.textContent
            if (correction && questionLabel.indexOf(correction.textContent) !== -1) {
              questionLabel = questionLabel.substring(0, questionLabel.indexOf(correction.textContent))
            }
            statistics.expected[title][questionLabel] = answers[name][i]
          }
          // now determine answers and their labels
          element.querySelectorAll('input:checked').forEach(node => {

            // remove eventual glued corretion
            let label = node.parentElement.textContent
            if (correction && label.indexOf(correction.textContent) !== -1) {
              label = label.substr(0, label.indexOf(correction.textContent))
            }
            statistics.result[title].labels.push(label.trim())
          })
          if (element.classList.contains('hasAnswer') && !element.classList.contains('quizz-bad')) {

            element.classList.add('quizz-good')
            statistics.result[title].evaluation = 'ok'

          }
        }
      })

      if (document.querySelector('input[name=\'csrfmiddlewaretoken\']')) {

        sendQuizzStatistics(form, statistics)
      }
      submitBtn.setAttribute('disabled', true);
      displayResultAfterSubmitButton(form)
      notAnswered.innerText = ''
      // not all questions answered
    } else {

      notAnswered.innerText = 'Veuillez répondre à toutes les questions'

    }
  })
})



