document.addEventListener('DOMContentLoaded', function () {
    const modal = new bootstrap.Modal(document.getElementById('infoModal'));
    modal.show();

    const btnUnderstand = document.getElementById('btnUnderstand');
    const floatingTextContainer = document.getElementById('floatingTextContent');
    const floatingTarget = document.getElementById('floatingTextTarget');
    const template = document.getElementById('noticeTextTemplate');


    btnUnderstand.addEventListener('click', () => {
      modal.hide();

      const clone = template.content.cloneNode(true);
      const floatingDiv = document.createElement('div');
      floatingDiv.className = 'floating-copy';
      floatingDiv.appendChild(clone);
      document.body.appendChild(floatingDiv);

      const rect = floatingTextContainer.getBoundingClientRect();
      floatingDiv.style.top = `${rect.top + window.scrollY}px`;
      floatingDiv.style.left = `${rect.left + window.scrollX}px`;
      floatingDiv.style.width = `${rect.width}px`;

      setTimeout(() => {
        floatingDiv.classList.add('fly-to-top');
      }, 100);

      setTimeout(() => {
        floatingTarget.innerHTML = template.innerHTML;
        floatingTarget.style.display = 'block';
        floatingDiv.remove();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }, 1300);
    });
  });

    