// Search bar functionality
const searchBar = document.getElementById('searchBar');

searchBar.addEventListener('input', () => {
    filterAccounts(searchBar.value);
});

function filterAccounts(searchText) {
    const accountCards = Array.from(accountsContainer.getElementsByClassName('account-card'));

    accountCards.forEach(card => {
        const displayName = card.querySelector('.card-title').textContent;
        const isVisible = displayName.toLowerCase().includes(searchText.toLowerCase());
        card.style.display = isVisible ? 'block' : 'none';
    });
}