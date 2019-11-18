const clearSearch = (reach) => {
    const clearButton = document.getElementById('search-clear');
    const searchInput = document.getElementById('search-term');
    if (clearButton) {
        clearButton.addEventListener('click', () => {
            searchInput.value = '';
        });

    }
};

export default clearSearch;
