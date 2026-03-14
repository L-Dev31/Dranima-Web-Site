function renderNewsPopupContent(item) {
    const contentEl = document.querySelector('.news-popup-content');
    if (!contentEl) return;
    contentEl.innerHTML = item.content || '';
}

function initNewsPopup() {
    const template = document.getElementById('news-popup-template');
    if (!template) return;

    const overlay = template.content.firstElementChild.cloneNode(true);
    document.body.appendChild(overlay);

    overlay.querySelector('.news-popup-close').addEventListener('click', closeNewsPopup);
    overlay.addEventListener('click', e => { if (e.target === overlay) closeNewsPopup(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeNewsPopup(); });
}

function openNewsPopup(item) {
    const overlay = document.querySelector('.news-popup-overlay');
    if (!overlay) return;
    const icon = item.type === 'update' ? 'images/UPD.png' : 'images/NEWS.png';
    overlay.querySelector('.news-popup-image img').src = item.image;
    overlay.querySelector('.news-popup-image img').alt = item.title;
    overlay.querySelector('.news-popup-icon img').src = icon;
    overlay.querySelector('.news-popup-title').textContent = item.title;
    overlay.querySelector('.news-popup-date').textContent = formatDate(item.date);
    overlay.querySelector('.news-popup-desc').textContent = item.description;
    renderNewsPopupContent(item);
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
}

function closeNewsPopup() {
    const overlay = document.querySelector('.news-popup-overlay');
    if (!overlay) return;
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
}

function createNewsCard(item, small = false) {
    const template = document.getElementById('news-card-template');
    if (!template) return document.createElement('div');

    const card = template.content.firstElementChild.cloneNode(true);
    if (small) card.classList.add('news-card--small');

    const icon = item.type === 'update' ? 'images/UPD.png' : 'images/NEWS.png';

    const img = card.querySelector('.news-card-image img');
    const title = card.querySelector('.news-card-title');
    const desc = card.querySelector('.news-card-desc');
    const date = card.querySelector('.news-card-date');
    const circleImg = card.querySelector('.news-card-circle img');

    if (img) {
        img.src = item.image;
        img.alt = item.title;
    }
    if (title) title.textContent = item.title;
    if (desc) desc.textContent = item.description;
    if (date) date.textContent = formatDate(item.date);
    if (circleImg) {
        circleImg.src = icon;
        circleImg.alt = '';
    }

    card.addEventListener('click', () => openNewsPopup(item));
    return card;
}

function createNewsListItem(item) {
    const template = document.getElementById('news-list-item-template');
    if (!template) return document.createElement('li');

    const li = template.content.firstElementChild.cloneNode(true);
    const title = li.querySelector('.news-list-title');
    const date = li.querySelector('.news-list-date');
    const link = li.querySelector('a');

    if (title) title.textContent = item.title;
    if (date) date.textContent = formatDate(item.date);

    if (link) {
        link.addEventListener('click', e => {
            e.preventDefault();
            openNewsPopup(item);
        });
    }

    return li;
}

function renderNewsColumn(items, cardContainerId, listId, showMoreId) {
    const cardContainer = document.getElementById(cardContainerId);
    const list = document.getElementById(listId);
    const showMore = document.getElementById(showMoreId);
    if (!cardContainer || !list || !showMore) return;

    const column = cardContainer.closest('.news-column');
    if (!column) return;

    if (!items || items.length === 0) {
        column.style.display = 'none';
        return;
    }

    column.style.display = '';
    cardContainer.appendChild(createNewsCard(items[0], true));

    const listItems = items.slice(1).map(item => createNewsListItem(item));
    listItems.forEach((li, idx) => {
        if (idx >= NEWS_LIST_MAX) {
            li.style.display = 'none';
        }
        list.appendChild(li);
    });

    const toggleShowMore = () => {
        const expanded = showMore.classList.toggle('expanded');
        showMore.textContent = expanded ? 'Show Less' : 'Show More';
        listItems.forEach((li, idx) => {
            if (idx >= NEWS_LIST_MAX) {
                li.style.display = expanded ? '' : 'none';
            }
        });
    };

    showMore.addEventListener('click', e => {
        e.preventDefault();
        toggleShowMore();
    });

    if (items.length > 1 + NEWS_LIST_MAX) {
        showMore.style.display = 'block';
    }
}

async function initNews() {
    const majorContainer = document.getElementById('major-news-container');
    if (!majorContainer) return;
    const news = await fetch('datas/news.json').then(r => r.json());
    news.sort((a, b) => new Date(b.date) - new Date(a.date));

    news.filter(n => n.important).forEach(n => majorContainer.appendChild(createNewsCard(n)));

    renderNewsColumn(
        news.filter(n => n.type === 'update'),
        'update-card-container', 'update-list', 'update-show-more'
    );
    renderNewsColumn(
        news.filter(n => n.type === 'announcement'),
        'announcement-card-container', 'announcement-list', 'announcement-show-more'
    );
}
