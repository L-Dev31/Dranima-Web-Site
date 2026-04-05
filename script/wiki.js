(() => {
    function renderWikiReferences(html, entries) {
        return html.replace(/@([\w-]+)/g, (match, refId) => {
            const entry = entries.find(e => e.id === refId);
            if (!entry) return match;

            const icon = entry.icon;
            const name = entry.name || refId;
            const escapedName = escapeHtml(name);
            const escapedIcon = icon ? escapeHtml(icon) : '';

            const iconHTML = escapedIcon ? `<img class="wiki-ref-icon" src="${escapedIcon}" alt="${escapedName} icon">` : '';
            const safeId = encodeURIComponent(entry.id);

            return `<a class="wiki-ref-link" href="wiki-page.html?id=${safeId}">${iconHTML}${escapedName}</a>`;
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
        const groups = originalGroups || chunkArray(normalCategories.map(c => c.id), 5);

        function createEntryLink(entry) {
            const link = document.createElement('a');
            link.className = 'wiki-entry-link';
            link.href = `wiki-page.html?id=${encodeURIComponent(entry.id)}`;

            const nameSpan = document.createElement('span');
            nameSpan.textContent = entry.name;

            if (entry.icon) {
                const img = document.createElement('img');
                img.className = 'wiki-entry-icon';
                img.src = entry.icon;
                img.alt = `${entry.name} icon`;
                link.appendChild(img);
            }

            link.appendChild(nameSpan);
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
                const heading = document.createElement('h2');
                heading.textContent = cat.name;
                header.appendChild(heading);
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
            const wrapper = document.createElement('div');
            wrapper.className = 'wiki-page-notfound';

            const heading = document.createElement('h2');
            heading.textContent = 'No entry specified';
            wrapper.appendChild(heading);

            const backLink = document.createElement('a');
            backLink.href = 'wiki.html';
            backLink.className = 'wiki-page-back';
            backLink.textContent = '← Back to Wiki';
            wrapper.appendChild(backLink);

            container.innerHTML = '';
            container.appendChild(wrapper);
            return;
        }

        const data = normalizeWikiData(await fetch('datas/wiki.json').then(r => r.json()));
        const entry = data.entries.find(e => e.id === entryId);

        if (!entry) {
            const wrapper = document.createElement('div');
            wrapper.className = 'wiki-page-notfound';

            const heading = document.createElement('h2');
            heading.textContent = 'Entry not found';
            wrapper.appendChild(heading);

            const msg = document.createElement('p');
            msg.style.color = '#fff';
            msg.style.marginBottom = '20px';
            msg.textContent = `The wiki entry "${entryId}" does not exist.`;
            wrapper.appendChild(msg);

            const backLink = document.createElement('a');
            backLink.href = 'wiki.html';
            backLink.className = 'wiki-page-back';
            backLink.textContent = '← Back to Wiki';
            wrapper.appendChild(backLink);

            container.innerHTML = '';
            container.appendChild(wrapper);
            return;
        }

        document.title = `${entry.name} - Wiki - Dranima`;


        const tocList = document.createElement('ul');
        entry.sections.forEach((section, index) => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = `#section-${index}`;
            a.textContent = section.title;
            li.appendChild(a);
            tocList.appendChild(li);
        });

        const pageHeader = document.createElement('div');
        pageHeader.className = 'wiki-page-header';

        const titleRow = document.createElement('div');
        titleRow.className = 'wiki-page-title-row';

        const titleIcon = document.createElement('img');
        titleIcon.className = 'wiki-page-title-icon';
        titleIcon.src = entry.icon || '';
        titleIcon.alt = `${entry.name} icon`;

        const titleH1 = document.createElement('h1');
        titleH1.textContent = entry.name;

        titleRow.appendChild(titleIcon);
        titleRow.appendChild(titleH1);

        const headerImage = document.createElement('img');
        headerImage.className = 'wiki-page-image';
        headerImage.src = entry.image || '';
        headerImage.alt = entry.name;

        pageHeader.appendChild(titleRow);
        pageHeader.appendChild(headerImage);

        const introP = document.createElement('p');
        introP.className = 'wiki-page-intro';
        introP.textContent = entry.intro || '';

        const tocWrapper = document.createElement('div');
        tocWrapper.className = 'wiki-page-toc';
        const tocTitle = document.createElement('h3');
        tocTitle.textContent = 'Summary';
        tocWrapper.appendChild(tocTitle);
        tocWrapper.appendChild(tocList);

        const sectionsContainer = document.createElement('div');
        entry.sections.forEach((section, index) => {
            const sectionEl = document.createElement('div');
            sectionEl.className = 'wiki-page-section';
            sectionEl.id = `section-${index}`;

            const sectionTitle = document.createElement('h2');
            sectionTitle.textContent = section.title;

            const sectionContent = document.createElement('div');
            sectionContent.className = 'wiki-page-section-content';
            sectionContent.innerHTML = sanitizeHtml(renderWikiReferences(section.content, data.entries));

            sectionEl.appendChild(sectionTitle);
            sectionEl.appendChild(sectionContent);
            sectionsContainer.appendChild(sectionEl);
        });

        const backLink = document.createElement('a');
        backLink.href = 'wiki.html';
        backLink.className = 'wiki-page-back';
        backLink.textContent = '← Back to Wiki';

        container.innerHTML = '';
        container.appendChild(pageHeader);
        container.appendChild(introP);
        container.appendChild(tocWrapper);
        container.appendChild(sectionsContainer);
        container.appendChild(backLink);
    }

    window.initWiki = initWiki;
    window.initWikiPage = initWikiPage;
})();
