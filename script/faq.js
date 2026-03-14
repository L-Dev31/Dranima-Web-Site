async function initFaq() {
    const list = document.getElementById('faq-list');
    const template = document.getElementById('faq-item-template');
    if (!list || !template) return;

    const items = await fetch('datas/faq.json').then(r => r.json());

    items.forEach(({ question, answer }) => {
        const details = template.content.firstElementChild.cloneNode(true);
        details.querySelector('.faq-question').textContent = question;
        details.querySelector('.faq-answer').textContent = answer;
        list.appendChild(details);
    });
}
