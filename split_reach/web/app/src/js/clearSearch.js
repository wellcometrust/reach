const clearSearch = (reach) => {
    let clearButton = document.getElementById('search-clear');
    let searchInput = document.getElementById('search-term');
    if (clearButton) {
        clearButton.addEventListener('click', () => {
            searchInput.value = '';
        });

    }
};

export default clearSearch;
