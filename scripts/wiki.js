(() => {
    function renderWikiReferences(html, entries) {
        return html.replace(/@\{([\w-]+)\}|@([\w-]+)/g, (match, bracedRefId, plainRefId) => {
            const refId = bracedRefId || plainRefId;
            const entry = entries.find(e => e.id === refId);
            if (!entry) return match;

            const escapedName = escapeHtml(entry.name || refId);
            const iconHTML = entry.icon
                ? `<img class="wiki-ref-icon" src="${escapeHtml(entry.icon)}" alt="${escapedName} icon">`
                : '';

            return `<a class="wiki-ref-link" href="wiki-page.html?id=${encodeURIComponent(entry.id)}">${iconHTML}${escapedName}</a>`;
        });
    }

    function renderWikiRichContent(rawHtml, entries) {
        const withRefs = renderWikiReferences(rawHtml || '', entries);
        const sanitized = sanitizeHtml(withRefs);

        const template = document.createElement('template');
        template.innerHTML = sanitized;
        template.content.querySelectorAll('table').forEach(table => {
            table.classList.add('wiki-table');
        });

        return template.innerHTML;
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
                sections: Array.isArray(entry.sections) ? entry.sections : []
            }))
        };
    }

    function chunkArray(arr, size) {
        const out = [];
        for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
        return out;
    }

    // Shared between initWiki and initWikiPage
    function createEntryLink(entry) {
        const link = document.createElement('a');
        link.className = 'wiki-entry-link';
        link.href = `wiki-page.html?id=${encodeURIComponent(entry.id)}`;

        if (entry.icon) {
            const img = document.createElement('img');
            img.className = 'wiki-entry-icon';
            img.src = entry.icon;
            img.alt = `${entry.name} icon`;
            link.appendChild(img);
        }

        const nameSpan = document.createElement('span');
        nameSpan.textContent = entry.name;
        link.appendChild(nameSpan);
        return link;
    }

    async function initWiki() {
        const container = document.getElementById('wiki-container');
        if (!container) return;

        const data = normalizeWikiData(await fetch('data/wiki.json').then(r => r.json()));
        const { categories, groups: originalGroups, entries } = data;
        const groups = originalGroups || chunkArray(categories.map(c => c.id), 5);

        function renderCategoryGroup(catGroup, groupClass) {
            const groupEl = document.createElement('div');
            groupEl.className = `wiki-group ${groupClass}`;

            catGroup.forEach(cat => {
                const col = document.createElement('div');
                col.className = 'wiki-column';

                const header = document.createElement('div');
                header.className = 'wiki-category-header';
                const heading = document.createElement('h2');
                heading.textContent = cat.name;
                header.appendChild(heading);
                col.appendChild(header);

                const list = document.createElement('div');
                list.className = 'wiki-entries-list';
                entries.filter(e => e.category === cat.id).forEach(e => list.appendChild(createEntryLink(e)));
                col.appendChild(list);

                groupEl.appendChild(col);
            });

            container.appendChild(groupEl);
        }

        container.innerHTML = '';
        groups.forEach(group => {
            const groupCats = group.map(id => categories.find(c => c.id === id)).filter(Boolean);
            if (groupCats.length) renderCategoryGroup(groupCats, groupCats.length > 1 ? 'wiki-group-multi' : 'wiki-group-single');
        });

        if (container.children.length === 0) {
            container.innerHTML = '<p style="text-align: center; font-size: 1.5rem; color: #fff; text-shadow: var(--shadow);">No results found.</p>';
        }
    }

    async function initWikiPage() {
        const container = document.getElementById('wiki-page-container');
        if (!container) return;

        const params = new URLSearchParams(window.location.search);
        const entryId = params.get('id');

        function renderNotFound(title, msg) {
            const wrapper = document.createElement('div');
            wrapper.className = 'wiki-page-notfound';

            const heading = document.createElement('h2');
            heading.textContent = title;
            wrapper.appendChild(heading);

            if (msg) {
                const p = document.createElement('p');
                p.style.color = '#fff';
                p.style.marginBottom = '20px';
                p.textContent = msg;
                wrapper.appendChild(p);
            }

            const backLink = document.createElement('a');
            backLink.href = 'wiki.html';
            backLink.className = 'wiki-page-back';
            backLink.textContent = '← Back to Wiki';
            wrapper.appendChild(backLink);

            container.innerHTML = '';
            container.appendChild(wrapper);
        }

        if (!entryId) return renderNotFound('No entry specified');

        const data = normalizeWikiData(await fetch('data/wiki.json').then(r => r.json()));
        const entry = data.entries.find(e => e.id === entryId);

        if (!entry) return renderNotFound('Entry not found', `The wiki entry "${entryId}" does not exist.`);

        document.title = `${entry.name} - Wiki - Dranima`;

        // Header
        const pageHeader = document.createElement('div');
        pageHeader.className = 'wiki-page-header';

        const titleRow = document.createElement('div');
        titleRow.className = 'wiki-page-title-row';

        if (entry.icon) {
            const titleIcon = document.createElement('img');
            titleIcon.className = 'wiki-page-title-icon';
            titleIcon.src = entry.icon;
            titleIcon.alt = `${entry.name} icon`;
            titleRow.appendChild(titleIcon);
        }

        const titleH1 = document.createElement('h1');
        titleH1.textContent = entry.name;
        titleRow.appendChild(titleH1);
        pageHeader.appendChild(titleRow);

        if (entry.image) {
            const headerImage = document.createElement('img');
            headerImage.className = 'wiki-page-image';
            headerImage.src = entry.image;
            headerImage.alt = entry.name;
            pageHeader.appendChild(headerImage);
        }

        container.innerHTML = '';
        container.appendChild(pageHeader);

        // Intro
        if (entry.intro) {
            const introBlock = document.createElement('div');
            introBlock.className = 'wiki-page-intro';
            introBlock.innerHTML = renderWikiRichContent(entry.intro, data.entries);
            container.appendChild(introBlock);
        }

        // TOC + Sections
        if (entry.sections.length > 0) {
            const tocWrapper = document.createElement('div');
            tocWrapper.className = 'wiki-page-toc';
            const tocTitle = document.createElement('h3');
            tocTitle.textContent = 'Summary';
            tocWrapper.appendChild(tocTitle);
            const tocList = document.createElement('ul');
            entry.sections.forEach((section, index) => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = `#section-${index}`;
                a.textContent = section.title;
                li.appendChild(a);
                tocList.appendChild(li);
            });
            tocWrapper.appendChild(tocList);
            container.appendChild(tocWrapper);

            const sectionsContainer = document.createElement('div');
            entry.sections.forEach((section, index) => {
                const sectionEl = document.createElement('div');
                sectionEl.className = 'wiki-page-section';
                sectionEl.id = `section-${index}`;

                const sectionTitle = document.createElement('h2');
                sectionTitle.textContent = section.title;

                const sectionContent = document.createElement('div');
                sectionContent.className = 'wiki-page-section-content';
                sectionContent.innerHTML = renderWikiRichContent(section.content, data.entries);

                sectionEl.appendChild(sectionTitle);
                sectionEl.appendChild(sectionContent);
                sectionsContainer.appendChild(sectionEl);
            });
            container.appendChild(sectionsContainer);
        }

        const backLink = document.createElement('a');
        backLink.href = 'wiki.html';
        backLink.className = 'wiki-page-back';
        backLink.textContent = '← Back to Wiki';
        container.appendChild(backLink);
    }

    window.initWiki = initWiki;
    window.initWikiPage = initWikiPage;
})();
