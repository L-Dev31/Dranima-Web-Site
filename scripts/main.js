(async () => {
    // Static fragments are independent — one failing must not block the others.
    await Promise.allSettled([loadNavbar(), loadFooter(), loadLoader()]);
    initLoader();

    if (typeof initNewsPopup === 'function') initNewsPopup();

    const initTasks = [];
    if (typeof initNews === 'function') initTasks.push(initNews());
    if (typeof initFaq === 'function') initTasks.push(initFaq());
    if (typeof initCredits === 'function') initTasks.push(initCredits());
    if (typeof initWiki === 'function') initTasks.push(initWiki());
    if (typeof initWikiPage === 'function') initTasks.push(initWikiPage());

    // allSettled: a single failed fetch/parse must not prevent the remaining
    // sections or the back-to-top button from initializing.
    const results = await Promise.allSettled(initTasks);
    results.forEach(r => {
        if (r.status === 'rejected') console.error('Page section init failed:', r.reason);
    });

    initBackToTop();
})();
