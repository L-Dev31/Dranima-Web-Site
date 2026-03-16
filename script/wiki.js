function renderWikiReferences(html, entries) {
    return html.replace(/@([\w-]+)/g, (match, refId) => {
        const entry = entries.find(e => e.id === refId);
        if (!entry) return match;
        const icon = entry.icon;
        const name = entry.name || refId;
        const iconHTML = icon ? `<img class="wiki-ref-icon" src="${icon}" alt="">` : '';
        return `<a class="wiki-ref-link" href="wiki-page.html?id=${entry.id}">${iconHTML}${name}</a>`;
    });
}
function normalizeWikiData(data) {
    return {
        ...data,
        categories: data.categories || [],
        groups: (Array.isArray(data.groups) && data.groups.length) ? data.groups : null,
        entries: (data.entries || []).map(entry => ({
            ...entry,
            id: entry.id,
            name: entry.name || entry.id,
            category: entry.category || null,
            icon: entry.icon || null,
            image: entry.image || null,
            intro: entry.intro || entry.preview || null,
            sections: Array.isArray(entry.sections) ? entry.sections : [],
            table_data: Array.isArray(entry.table_data) ? entry.table_data : null
        }))
    };
}

function chunkArray(arr, size) {
    const out = [];
    for (let i = 0; i < arr.length; i += size) {
        out.push(arr.slice(i, i + size));
    }
    return out;
}

async function initWiki() {
    const container = document.getElementById('wiki-container');
    if (!container) return;

    const data = normalizeWikiData(await fetch('datas/wiki.json').then(r => r.json()));
    const { categories, groups: originalGroups, entries } = data;
    const tableCategories = categories.filter(c => c.is_table);
    const normalCategories = categories.filter(c => !c.is_table);
    const groups = originalGroups || chunkArray(normalCategories.map(c => c.id), 4);

    function createEntryLink(entry) {
        const link = document.createElement('a');
        link.className = 'wiki-entry-link';
        link.href = `wiki-page.html?id=${entry.id}`;
        if (entry.icon) {
            link.innerHTML = `<img class="wiki-entry-icon" src="${entry.icon}" alt=""><span>${entry.name}</span>`;
        } else {
            link.textContent = entry.name;
        }
        return link;
    }

    function renderCategoryGroup(catGroup, groupClass) {
        const groupEl = document.createElement('div');
        groupEl.className = `wiki-group ${groupClass}`;
        catGroup.forEach(cat => {
            const col = document.createElement('div');
            col.className = 'wiki-column';
            const header = document.createElement('div');
            header.className = `wiki-category-header${cat.is_table ? ' wiki-table-header' : ''}`;
            header.innerHTML = `<h2>${cat.name}</h2>`;
            col.appendChild(header);

            if (cat.is_table) {
                const table = document.createElement('table');
                table.className = 'wiki-table';

                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                (cat.columns || []).forEach(colTitle => {
                    const th = document.createElement('th');
                    th.textContent = colTitle;
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);
                table.appendChild(thead);

                const tbody = document.createElement('tbody');
                entries
                    .filter(e => e.category === cat.id && Array.isArray(e.table_data))
                    .forEach(entry => {
                        const row = document.createElement('tr');
                        const rowData = entry.table_data;

                        (cat.columns || []).forEach((_, colIndex) => {
                            const cell = document.createElement('td');
                            const cellValue = rowData[colIndex];

                            if (colIndex === 1 && typeof cellValue === 'string') {
                                const refEntry = entries.find(e => e.id === cellValue);
                                if (refEntry) {
                                    const link = createEntryLink(refEntry);
                                    cell.appendChild(link);
                                } else {
                                    cell.textContent = cellValue;
                                }
                            } else if (colIndex === 2 && typeof cellValue === 'string') {
                                const refEntry = entries.find(e => e.id === cellValue);
                                if (refEntry) {
                                    const link = document.createElement('a');
                                    link.className = 'wiki-entry-link';
                                    link.href = `wiki-page.html?id=${refEntry.id}`;
                                    link.textContent = refEntry.name;
                                    cell.appendChild(link);
                                } else {
                                    cell.textContent = cellValue;
                                }
                            } else {
                                cell.textContent = cellValue ?? '';
                            }

                            row.appendChild(cell);
                        });

                        tbody.appendChild(row);
                    });
                table.appendChild(tbody);
                col.appendChild(table);
            } else {
                const list = document.createElement('div');
                list.className = 'wiki-entries-list';
                entries.filter(e => e.category === cat.id).forEach(entry => list.appendChild(createEntryLink(entry)));
                col.appendChild(list);
            }

            groupEl.appendChild(col);
        });
        container.appendChild(groupEl);
    }

    function renderWiki() {
        container.innerHTML = '';

        // Render normal categories first
        (groups || normalCategories.map(c => [c.id])).forEach(group => {
            const groupCats = group.map(id => normalCategories.find(c => c.id === id)).filter(Boolean);
            renderCategoryGroup(groupCats, groupCats.length > 1 ? 'wiki-group-multi' : 'wiki-group-single');
        });

        // Render tables afterwards (e.g. dradeck)
        if (tableCategories.length) {
            const tableGroups = chunkArray(tableCategories, 2);
            tableGroups.forEach(group => renderCategoryGroup(group, 'wiki-group-multi'));
        }

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
            <div class="wiki-page-section-content">${renderWikiReferences(section.content, data.entries)}</div>
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
        <p class="wiki-page-intro">${entry.intro || ''}</p>
        <div class="wiki-page-toc">
            <h3>Summary</h3>
            <ul>${tocHTML}</ul>
        </div>
        ${sectionsHTML}
        <a href="wiki.html" class="wiki-page-back">← Back to Wiki</a>
    `;
}
