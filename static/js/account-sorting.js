// Sorting cards by rank
const RANKS_ORDER = [
    'Iron 1', 'Iron 2', 'Iron 3',
    'Bronze 1', 'Bronze 2', 'Bronze 3',
    'Silver 1', 'Silver 2', 'Silver 3',
    'Gold 1', 'Gold 2', 'Gold 3',
    'Platinum 1', 'Platinum 2', 'Platinum 3',
    'Diamond 1', 'Diamond 2', 'Diamond 3',
    'Ascendant 1', 'Ascendant 2', 'Ascendant 3',
    'Immortal 1', 'Immortal 2', 'Immortal 3',
    'Radiant'
];

const accountsContainer = document.getElementById('accountsContainer');
const sortBtn = document.getElementById('sortBtn');

let sortOrder = 'asc'; // Default sort order

sortBtn.addEventListener('click', () => {
    sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    sortBtn.textContent = `Sort: ${sortOrder === 'asc' ? 'Ascending' : 'Descending'}`;
    sortAccounts();
});

sortAccounts();

function sortAccounts() {
    const accountCards = Array.from(accountsContainer.getElementsByClassName('account-card'));

    accountCards.sort((a, b) => {
        const rankA = a.getAttribute('data-rank');
        const rankB = b.getAttribute('data-rank');
        const orderA = RANKS_ORDER.indexOf(rankA);
        const orderB = RANKS_ORDER.indexOf(rankB);

        if (orderA === -1) return 1;
        if (orderB === -1) return -1;
        return sortOrder === 'asc' ? orderA - orderB : orderB - orderA;
    });

    for (const card of accountCards) {
        accountsContainer.appendChild(card);
    }
}