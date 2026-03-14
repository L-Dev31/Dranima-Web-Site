async function initCredits() {
    const container = document.getElementById('credits-container');
    const guestContainer = document.getElementById('credits-guest-container');
    if (!container && !guestContainer) return;

    const creditsData = await fetch('datas/credits.json').then(r => r.json());
    const { categories, guests, team } = creditsData;

    const teamMap = new Map((team || []).map(member => [member.id, member]));

    if (container) {
        categories.forEach(({ title, members }) => {
            const category = document.createElement('div');
            category.className = 'credits-category';
            category.innerHTML = `<h2>${title}</h2>`;

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
                const displayName = alias ? `${name}<br>(${alias})` : name;
                const rolesHTML = (roles || []).map(r => `<span class="credit-role">${r}</span>`).join('');
                card.innerHTML = `
                    <img class="credit-pfp" src="${image || 'images/template.png'}" alt="${name}">
                    <span class="credit-name">${displayName}</span>
                    ${rolesHTML}
                `;
                row.appendChild(card);
            });

            category.appendChild(row);
            container.appendChild(category);
        });
    }

    if (guestContainer) {
        guests.forEach(name => {
            const span = document.createElement('span');
            span.textContent = `- ${name}`;
            guestContainer.appendChild(span);
        });
    }
}
