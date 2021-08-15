/**
 * ZDS ajax library
 * This library was created to reduce code duplication when we use ajax and ease up the JQuery removal
 * We use fetch API
 */
class ZDSAjax {
  constructor() {
    const csrfInput = document.querySelector("input[name='csrfmiddlewaretoken']")
    if (csrfInput !== null) {
      this._crsf = csrfInput.getAttribute('value')
    }
    else {
      this._csrf = null
    }
  }

  get(url, dataCallback, errorCallback = (error) => console.error(error)) {
    const headers = new Headers()
    headers.append('Accept', 'application/json')
    if (this._csrf !== null) {
      headers.append('X-CSRFToken', this._crsf)
    }
    headers.append('X-REQUESTED-WITH', 'XMLHttpRequest')
    const init = {
      method: 'GET',
      headers: headers,
      mode: 'cors',
      cache: 'default'
    }
    fetch(new Request(url, init), init).then(response => {
      if (response.ok) {
        return Promise.resolve(response.json())
      }
      throw response.error()
    }).then(dataCallback).catch(errorCallback)
  }

  put(url, jsonOrFormData, dataCallback, errorCallback) {
    return this._sendRequestWithData(jsonOrFormData, 'PUT', url, dataCallback, errorCallback)
  }

  post(url, jsonOrFormData, dataCallback, errorCallback) {
    return this._sendRequestWithData(jsonOrFormData, 'POST', url, dataCallback, errorCallback)
  }

  _sendRequestWithData(jsonOrFormData, method, url, dataCallback, errorCallback) {
    const headers = new Headers()
    headers.append('Accept', 'application/json')
    if (this._csrf !== null) {
      headers.append('X-CSRFToken', this._crsf)
    }
    headers.append('X-REQUESTED-WITH', 'XMLHttpRequest')
    const init = {
      method: method,
      headers: headers,
      mode: 'cors',
      cache: 'default',
      body: jsonOrFormData
    }
    return fetch(url, init).then(response => {
      return Promise.resolve(response.json())
    }).then(dataCallback).catch(errorCallback)
  }
}
window.ajax = new ZDSAjax()
