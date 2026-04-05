const LOADER_THRESHOLD = 200;
const NEWS_LIST_MAX = 5;
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function sanitizeHtml(html) {
    const template = document.createElement('template');
    template.innerHTML = String(html);

    const disallowedTags = new Set(['script', 'style', 'iframe', 'object', 'embed', 'link']);
    const walker = document.createTreeWalker(template.content, NodeFilter.SHOW_ELEMENT, null);

    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (disallowedTags.has(node.nodeName.toLowerCase())) {
            node.remove();
            continue;
        }

        for (const attr of Array.from(node.attributes)) {
            const name = attr.name.toLowerCase();
            const value = (attr.value || '').trim();
            if (name.startsWith('on') || value.toLowerCase().startsWith('javascript:') || value.toLowerCase().startsWith('vbscript:')) {
                node.removeAttribute(attr.name);
            }
        }
    }

    return template.innerHTML;
}

function getCurrentPage() {
    return location.pathname.split('/').pop() || 'index.html';
}

async function loadFragment(src, container) {
    if (typeof container === 'string') container = document.getElementById(container);
    if (!container) return;

    try {
        const response = await fetch(src);
        if (!response.ok) return;
        const html = await response.text();
        container.innerHTML = sanitizeHtml(html);
    } catch (err) {
        console.warn('Failed to load fragment', src, err);
    }
}

async function loadNavbar() {
    const container = document.getElementById('navbar-container');
    if (!container) return;

    await loadFragment('assets/navbar.html', container);

    const page = getCurrentPage();
    const isHomepage = page === 'index.html' || page === '';

    document.querySelectorAll('.navbar-links a').forEach(link => {
        const href = link.getAttribute('href');
        if (isHomepage && href && href.startsWith('index.html#')) {
            link.setAttribute('href', '#' + href.split('#')[1]);
        }
    });

    initNavbar();
}

function initNavbar() {
    const page = getCurrentPage();
    document.querySelectorAll('.navbar-links a').forEach(link => {
        const href = link.getAttribute('href');
        const isActive =
            (page === 'index.html' && href === '#main') ||
            (page === 'credits.html' && href === 'credits.html') ||
            (page === 'project.html' && href === 'project.html') ||
            (page === 'wiki.html' && href === 'wiki.html');

        link.classList.toggle('active', isActive);
    });

    const navbar = document.querySelector('.navbar');
    const toggle = document.querySelector('.navbar-toggle');
    const menuSection = document.querySelector('.navbar-menu-mobile');

    if (menuSection) document.body.appendChild(menuSection);
    if (toggle) document.body.appendChild(toggle);

    const closeMenu = () => {
        if (!menuSection) return;
        menuSection.classList.remove('open');
        menuSection.setAttribute('aria-hidden', 'true');
        if (toggle) {
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', 'Open menu');
        }
    };

    const openMenu = () => {
        if (!menuSection) return;
        menuSection.classList.add('open');
        menuSection.setAttribute('aria-hidden', 'false');
        if (toggle) {
            toggle.setAttribute('aria-expanded', 'true');
            toggle.setAttribute('aria-label', 'Close menu');
        }
    };

    if (navbar && toggle && menuSection) {
        toggle.addEventListener('click', () => {
            if (menuSection.classList.contains('open')) {
                closeMenu();
            } else {
                openMenu();
            }
        });

        menuSection.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });

        // keep menu sticky until the toggle is pressed; links still close it
        // (no outside-click or Escape auto-close so it behaves like a persistent top menu)
    }
}

async function loadLoader() {
    const container = document.getElementById('loader-container');
    if (!container) return;
    await loadFragment('assets/loader.html', container);
}

async function loadFooter() {
    const container = document.getElementById('footer-container');
    if (!container) return;
    await loadFragment('assets/footer.html', container);
}

function initLoader() {
    const loader = document.getElementById('loader');
    if (!loader) return;

    const dismiss = () => {
        const el = document.getElementById('loader');
        if (!el) return;
        // If the loader was never shown, just remove it immediately to avoid a flash
        if (!el.classList.contains('loader-visible')) {
            el.remove();
            return;
        }

        el.classList.add('loader-exit');
        setTimeout(() => el.remove(), 1800);
    };

    const showLoader = () => {
        const el = document.getElementById('loader');
        if (!el) return;
        el.classList.add('loader-visible');
    };

    if (document.readyState === 'complete') {
        dismiss();
    } else {
        window.addEventListener('load', dismiss, { once: true });
        setTimeout(() => {
            const el = document.getElementById('loader');
            if (el && document.readyState !== 'complete') {
                showLoader();
            }
        }, LOADER_THRESHOLD);
    }
}

function formatDate(iso) {
    const d = new Date(iso);
    if (Number.isNaN(d.valueOf())) return iso;
    return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

function lockBodyScroll() {
    if (document.body.classList.contains('body--modal-open')) return;
    document.body.classList.add('body--modal-open');
}

function unlockBodyScroll() {
    if (!document.body.classList.contains('body--modal-open')) return;
    document.body.classList.remove('body--modal-open');
}

function initBackToTop() {
    const id = 'back-to-top';
    let btn = document.getElementById(id);
    if (!btn) {
        btn = document.createElement('img');
        btn.id = id;
        btn.src = 'images/UP.png';
        btn.alt = 'Back to top';
        btn.setAttribute('role', 'button');
        btn.setAttribute('tabindex', '0');
        document.body.appendChild(btn);
    }

    const showThreshold = 120;

    const updateVisibility = () => {
        btn.classList.toggle('show', window.scrollY > showThreshold);
    };

    window.addEventListener('scroll', updateVisibility, { passive: true });
    btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    btn.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            btn.click();
        }
    });
    updateVisibility();
}

window.lockBodyScroll = lockBodyScroll;
window.unlockBodyScroll = unlockBodyScroll;
