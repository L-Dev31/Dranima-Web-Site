const LOADER_THRESHOLD = 200;
const NEWS_LIST_MAX = 5;
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function getCurrentPage() {
    return location.pathname.split('/').pop() || 'index.html';
}

async function loadFragment(src, container) {
    if (typeof container === 'string') container = document.getElementById(container);
    if (!container) return;
    const html = await fetch(src).then(r => r.text());
    container.innerHTML = html;
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
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
    };

    const openMenu = () => {
        if (!menuSection) return;
        menuSection.classList.add('open');
        menuSection.setAttribute('aria-hidden', 'false');
        if (toggle) toggle.setAttribute('aria-expanded', 'true');
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
    const d = new Date(iso + 'T00:00:00');
    return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
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
    updateVisibility();
}