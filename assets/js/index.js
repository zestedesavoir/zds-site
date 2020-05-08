(function() {
  document.documentElement.classList.add('js')

  document.querySelectorAll('template[tpl-request]').forEach(function (template) {
    template.addEventListener('template-changed', function (e) {
      const t = 'parentNode'
      const ul = template[t]
      const count = ul[t][t].querySelector('.notif-count')
      count.textContent = ul.children.length -1
      count.classList.toggle('hidden', !(ul.children.length - 1));
    }, false);
  });
})()
