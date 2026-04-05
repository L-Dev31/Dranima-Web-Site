(() => {
    async function initCredits() {
        const container = document.getElementById('credits-container');
        const guestContainer = document.getElementById('credits-guest-container');
        if (!container && !guestContainer) return;

        const creditsData = await fetch('data/credits.json').then(r => r.json());
        const { categories, guests, team } = creditsData;

        const teamMap = new Map((team || []).map(member => [member.id, member]));

        if (container) {
            categories.forEach(({ title, members }) => {
                const category = document.createElement('div');
                category.className = 'credits-category';

                const heading = document.createElement('h2');
                heading.textContent = title;
                category.appendChild(heading);

                const row = document.createElement('div');
                row.className = 'credits-row';

                members.forEach((creditItem) => {
                    const memberData = teamMap.get(creditItem.id) || {};

                    const name = memberData.name || creditItem.id;
                    const alias = memberData.alias;
                    const image = memberData.image;
                    const link = memberData.link;
                    const roles = creditItem.roles;

                    const card = document.createElement(link ? 'a' : 'div');
                    card.className = 'credit-card';
                    if (link) {
                        card.href = link;
                        card.target = '_blank';
                        card.style.textDecoration = 'none';
                        card.style.color = 'inherit';
                    }

                    const img = document.createElement('img');
                    img.className = 'credit-pfp';
                    img.src = image || 'images/template.png';
                    img.alt = name;
                    card.appendChild(img);

                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'credit-name';
                    nameSpan.innerHTML = alias ? `${escapeHtml(name)}<br>(${escapeHtml(alias)})` : escapeHtml(name);
                    card.appendChild(nameSpan);

                    (roles || []).forEach(role => {
                        const roleSpan = document.createElement('span');
                        roleSpan.className = 'credit-role';
                        roleSpan.textContent = role;
                        card.appendChild(roleSpan);
                    });

                    row.appendChild(card);
                });

                category.appendChild(row);
                container.appendChild(category);
            });
        }

        if (guestContainer) {
            guests.forEach(guest => {
                const name = typeof guest === 'string' ? guest : guest.name || '';
                const link = typeof guest === 'object' && guest.link ? guest.link : null;

                const span = document.createElement('span');
                span.className = 'guest-item';

                if (link && link !== 'none') {
                    const a = document.createElement('a');
                    a.href = link;
                    a.target = '_blank';
                    a.rel = 'noopener noreferrer';
                    a.textContent = `- ${name}`;
                    span.appendChild(a);
                } else {
                    span.textContent = `- ${name}`;
                }

                guestContainer.appendChild(span);
            });
        }
    }

    window.initCredits = initCredits;
})();
