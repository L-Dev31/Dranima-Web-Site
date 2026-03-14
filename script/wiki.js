function normalizeWikiData(data) {
    const defaultEntry = {
        icon: 'images/template.png',
        image: 'images/template.png',
        preview: '',
        sections: [],
        ...(data.defaults?.entry || {})
    };

    return {
        ...data,
        categories: data.categories || [],
        groups: data.groups || [],
        entries: (data.entries || []).map(entry => ({
            ...defaultEntry,
            ...entry,
            sections: Array.isArray(entry.sections)
                ? entry.sections
                : [...defaultEntry.sections]
        }))
    };
}

async function initWiki() {
    const container = document.getElementById('wiki-container');
    if (!container) return;

    const data = normalizeWikiData(await fetch('datas/wiki.json').then(r => r.json()));
    const { categories, groups, entries } = data;

    function createEntryLink(entry) {
        const link = document.createElement('a');
        link.className = 'wiki-entry-link';
        link.href = `wiki-page.html?id=${entry.id}`;
        link.innerHTML = `<img class="wiki-entry-icon" src="${entry.icon}" alt=""><span>${entry.name}</span>`;
        return link;
    }

    function renderWiki() {
        container.innerHTML = '';

        (groups || categories.map(c => [c.id])).forEach(group => {
            const groupCats = group.map(id => categories.find(c => c.id === id)).filter(Boolean);
            const isMulti = groupCats.length > 1;

            const groupEl = document.createElement('div');
            groupEl.className = `wiki-group ${isMulti ? 'wiki-group-multi' : 'wiki-group-single'}`;

            if (isMulti) {
                groupCats.forEach(cat => {
                    const col = document.createElement('div');
                    col.className = 'wiki-column';

                    const header = document.createElement('div');
                    header.className = 'wiki-category-header';
                    header.innerHTML = `<h2>${cat.name}</h2>`;
                    col.appendChild(header);

                    const list = document.createElement('div');
                    list.className = 'wiki-entries-list';
                    entries.filter(e => e.category === cat.id).forEach(entry => list.appendChild(createEntryLink(entry)));
                    col.appendChild(list);
                    groupEl.appendChild(col);
                });
            } else {
                const cat = groupCats[0];
                if (!cat) return;
                const catEntries = entries.filter(e => e.category === cat.id);

                const header = document.createElement('div');
                header.className = 'wiki-category-header';
                header.innerHTML = `<h2>${cat.name}</h2>`;
                groupEl.appendChild(header);

                const grid = document.createElement('div');
                grid.className = 'wiki-entries-grid';
                catEntries.forEach(entry => grid.appendChild(createEntryLink(entry)));
                groupEl.appendChild(grid);
            }

            container.appendChild(groupEl);
        });

        if (container.children.length === 0) {
            container.innerHTML = '<p style="text-align: center; font-size: 1.5rem; color: #fff; text-shadow: var(--shadow);">No results found.</p>';
        }
    }

    renderWiki();
}

async function initWikiPage() {
    const container = document.getElementById('wiki-page-container');
    if (!container) return;

    const params = new URLSearchParams(window.location.search);
    const entryId = params.get('id');

    if (!entryId) {
        container.innerHTML = `
            <div class="wiki-page-notfound">
                <h2>No entry specified</h2>
                <a href="wiki.html" class="wiki-page-back">← Back to Wiki</a>
            </div>
        `;
        return;
    }

    const data = normalizeWikiData(await fetch('datas/wiki.json').then(r => r.json()));
    const entry = data.entries.find(e => e.id === entryId);

    if (!entry) {
        container.innerHTML = `
            <div class="wiki-page-notfound">
                <h2>Entry not found</h2>
                <p style="color: #fff; margin-bottom: 20px;">The wiki entry "${entryId}" does not exist.</p>
                <a href="wiki.html" class="wiki-page-back">← Back to Wiki</a>
            </div>
        `;
        return;
    }

    document.title = `${entry.name} - Wiki - Dranima`;

    const tocHTML = entry.sections.map((section, index) => 
        `<li><a href="#section-${index}">${section.title}</a></li>`
    ).join('');

    const sectionsHTML = entry.sections.map((section, index) => `
        <div class="wiki-page-section" id="section-${index}">
            <h2>${section.title}</h2>
            <div class="wiki-page-section-content">${section.content}</div>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="wiki-page-header">
            <div class="wiki-page-title-row">
                <img class="wiki-page-title-icon" src="${entry.icon}" alt="">
                <h1>${entry.name}</h1>
            </div>
            <img class="wiki-page-image" src="${entry.image}" alt="${entry.name}">
        </div>
        <p class="wiki-page-preview">${entry.preview}</p>
        <div class="wiki-page-toc">
            <h3>Summary</h3>
            <ul>${tocHTML}</ul>
        </div>
        ${sectionsHTML}
        <a href="wiki.html" class="wiki-page-back">← Back to Wiki</a>
    `;
}
