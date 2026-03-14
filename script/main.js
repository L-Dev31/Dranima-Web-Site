(async () => {
    await Promise.all([loadNavbar(), loadFooter(), loadLoader()]);
    initLoader();

    if (typeof initNewsPopup === 'function') initNewsPopup();

    const initTasks = [];
    if (typeof initNews === 'function') initTasks.push(initNews());
    if (typeof initFaq === 'function') initTasks.push(initFaq());
    if (typeof initCredits === 'function') initTasks.push(initCredits());
    if (typeof initWiki === 'function') initTasks.push(initWiki());
    if (typeof initWikiPage === 'function') initTasks.push(initWikiPage());

    await Promise.all(initTasks);
    initBackToTop();
})();
