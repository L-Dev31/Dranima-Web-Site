(() => {
    let lastFocused = null;

    function renderNewsPopupContent(item) {
        const contentEl = document.querySelector('.news-popup-content');
        if (!contentEl) return;
        contentEl.innerHTML = sanitizeHtml(item.content || '');
    }

    function trapFocus(e, container) {
        if (!container) return;
        const focusables = container.querySelectorAll(
            'a[href], button:not([disabled]), input, textarea, select, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusables.length) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    }

    function initNewsPopup() {
        const template = document.getElementById('news-popup-template');
        if (!template) return;

        const overlay = template.content.firstElementChild.cloneNode(true);
        document.body.appendChild(overlay);

        overlay.querySelector('.news-popup-close').addEventListener('click', closeNewsPopup);
        overlay.addEventListener('click', e => { if (e.target === overlay) closeNewsPopup(); });

        document.addEventListener('keydown', e => {
            if (!overlay.classList.contains('active')) return;
            if (e.key === 'Escape') {
                closeNewsPopup();
            } else if (e.key === 'Tab') {
                trapFocus(e, overlay.querySelector('.news-popup'));
            }
        });
    }

    function openNewsPopup(item) {
        const overlay = document.querySelector('.news-popup-overlay');
        if (!overlay) return;
        lastFocused = document.activeElement;
        const icon = item.category === 'update' ? 'images/UPD.png' : 'images/NEWS.png';
        const popupImage = overlay.querySelector('.news-popup-image img');
        popupImage.src = item.image;
        popupImage.alt = item.title;
        overlay.querySelector('.news-popup-icon img').src = icon;
        overlay.querySelector('.news-popup-title').textContent = item.title;
        overlay.querySelector('.news-popup-date').textContent = formatDate(item.date);
        overlay.querySelector('.news-popup-desc').textContent = item.description;
        renderNewsPopupContent(item);
        overlay.classList.add('active');
        if (typeof window.lockBodyScroll === 'function') {
            window.lockBodyScroll();
        } else {
            document.body.classList.add('body--modal-open');
        }
        const popup = overlay.querySelector('.news-popup');
        if (popup) popup.focus();
    }

    function closeNewsPopup() {
        const overlay = document.querySelector('.news-popup-overlay');
        if (!overlay) return;
        overlay.classList.remove('active');
        if (typeof window.unlockBodyScroll === 'function') {
            window.unlockBodyScroll();
        } else {
            document.body.classList.remove('body--modal-open');
        }
        if (lastFocused && typeof lastFocused.focus === 'function') {
            lastFocused.focus();
        }
        lastFocused = null;
    }

    function createNewsCard(item, small = false) {
        const template = document.getElementById('news-card-template');
        if (!template) return document.createElement('div');

        const card = template.content.firstElementChild.cloneNode(true);
        if (small) card.classList.add('news-card--small');

        const icon = item.category === 'update' ? 'images/UPD.png' : 'images/NEWS.png';

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
            circleImg.alt = item.category === 'update' ? 'Update icon' : 'Announcement icon';
        }

        card.setAttribute('aria-label', `Open news item: ${item.title}`);
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
            if (idx >= 3) {
                li.style.display = 'none';
            }
            list.appendChild(li);
        });

        const toggleShowMore = () => {
            const expanded = showMore.classList.toggle('expanded');
            showMore.textContent = expanded ? 'Show Less' : 'Show More';
            listItems.forEach((li, idx) => {
                if (idx >= 3) {
                    li.style.display = expanded ? '' : 'none';
                }
            });
        };

        showMore.addEventListener('click', e => {
            e.preventDefault();
            toggleShowMore();
        });

        // 1 card + 3 list items
        if (items.length > 1 + 3) {
            showMore.style.display = 'block';
        }
    }

    async function initNews() {
        const majorContainer = document.getElementById('major-news-container');
        if (!majorContainer) return;
        const news = await fetch('data/news.json').then(r => r.json());
        const byDateDescending = (a, b) => new Date(b.date) - new Date(a.date);
        const announcements = (news.announcement || []).map(item => ({ ...item, category: 'announcement' }))
            .sort(byDateDescending);
        const updates = (news.update || []).map(item => ({ ...item, category: 'update' }))
            .sort(byDateDescending);

        announcements.forEach(item => majorContainer.appendChild(createNewsCard(item)));

        renderNewsColumn(
            updates,
            'update-card-container', 'update-list', 'update-show-more'
        );
        renderNewsColumn(
            announcements,
            'announcement-card-container', 'announcement-list', 'announcement-show-more'
        );
    }

    window.initNews = initNews;
    window.initNewsPopup = initNewsPopup;
})();
