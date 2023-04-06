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

 */


var currentURL = window.location.href;

if (currentURL.includes("forums")) {
  
    let indeX = 0;
    function Makesurvey(inputDomElementList) {


        inputDomElementList.forEach((rb) => {

        
        const ulWrapperElement = rb.parentElement.parentElement
        // we give the ui an id to find the element in a more effective way later when the users answer the questions
        if (!ulWrapperElement.getAttribute('id')) {
            ulWrapperElement.setAttribute('id', 'id-' + (indeX++))
        }

        rb.setAttribute('name', ulWrapperElement.getAttribute('id'))
        rb.setAttribute('type', 'radio')

        const questionBlock = ulWrapperElement.parentElement.parentElement
        questionBlock.setAttribute('data-name', rb.getAttribute('name'))


        rb.disabled = false
        rb.checked = false

        })
    }


    function initializeRadio() {
        const radio  = document.querySelectorAll('.custom-block-quizz input');
        Makesurvey(radio)

    }

    const initializePipeline = [initializeRadio]


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

    let idCounter = 0

    function injectForms(survey) {


        const form = document.createElement('form')
        form.classList.add('quizz')
  
        
        const submit = document.createElement('button')
        submit.innerText = 'Voter'

        const cancel = document.createElement('button')
        cancel.innerText = 'Annuler'
        
        submit.classList.add('btn', 'btn-submit')
        submit.setAttribute('id', `my-button-${idCounter}`);
  
        cancel.classList.add('btn', 'btn-cancel')
        cancel.setAttribute('id', `my-button-cancel-${idCounter}`);
  
        const notAnswered = document.createElement('p')
        notAnswered.classList.add('notAnswered')

        // form.method = 'POST'
        // form.setAttribute('action', '')
        form.setAttribute('id', `my-form-${idCounter}`);
        idCounter++;

        form.appendChild(submit)
        form.appendChild(cancel)
        form.appendChild(notAnswered)
        survey.appendChild(form)
    
      }


      function displayResultAfterSubmitButton(quizz,result) {

      
        const inputs  = quizz.querySelectorAll('.custom-block-quizz input');
      
        for (let input of inputs) {
      
        }
      
      }
    
    initializePipeline.forEach(func => func())

    document.querySelectorAll('div.custom-block-quizz').forEach(div => {
        injectForms(div)
    })

    document.querySelectorAll('div.custom-block-quizz').forEach(div => {
        div.addEventListener('click',() => {
            const id =  event.target.id;
            const button = div.querySelector(id);
            // const submitBtn = div.querySelector('.btn-submit');
            // const cancelBtn = div.querySelector('.btn-cancel');
            console.log(id);
        
        })
    })
      
}


