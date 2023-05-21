/* ===== Zeste de Savoir ====================================================
   Manage Claps for publishable contents
   ========================================================================== */

class Clap {

  constructor(clapsElement) {
    this.clapButtonElement = clapsElement.querySelector(".clap")
    this.nbClapsElement = clapsElement.querySelector(".nb_claps")
    this.nbClaps = parseInt(this.nbClapsElement.innerText)
    this.already_clapped()
        .then(v => this.hasClapped = v)
        .then(v => this.refreshDisplay())
    this.clapButtonElement.addEventListener("click", e => {
      this.addOrDeleteClap()
    })
  }

  async addOrDeleteClap() {
    this.hasClapped = await this.already_clapped()
    if (this.hasClapped) {
      await this.remove_clap()
    } else {
      await this.give_clap()
    }
    this.refreshDisplay()
  }

  refreshDisplay() {
    this.nbClapsElement.innerText = this.nbClaps
    if (this.hasClapped) {
      this.clapButtonElement.classList.add("clapped")
    } else {
      this.clapButtonElement.classList.remove("clapped")
    }
  }

  async already_clapped() {
    const url = this.clapButtonElement.dataset.clapUri
    const csrf = document.querySelector("input[name=csrfmiddlewaretoken]").value
    const response = await fetch(url, {
      method: "GET",
      mode: "same-origin",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": csrf
      }
    })
    if (response.status === 404) {
      return false
    }
    return true
  }

  async remove_clap() {
    const url = this.clapButtonElement.dataset.clapUri
    const csrf = document.querySelector("input[name=csrfmiddlewaretoken]").value
    const response = await fetch(url, {
      method: "DELETE",
      mode: "same-origin",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": csrf
      }
    })
    if (response.ok) {
      this.nbClaps -= 1
      this.hasClapped = false
    }
  }

  async give_clap() {
    const url = this.clapButtonElement.dataset.clapUri
    const csrf = document.querySelector("input[name=csrfmiddlewaretoken]").value
    const response = await fetch(url, {
      method: "POST",
      mode: "same-origin",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": csrf
      }
    })
    if (response.ok) {
      this.nbClaps = this.nbClaps + 1
      this.hasClapped = true
    }
  }
}

const clapsElements = document.querySelectorAll(".claps")
clapsElements.forEach(e => new Clap(e))
