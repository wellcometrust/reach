const clearSearch = (targetElement, clearButton) => {
    clearButton.addEventListener('click', () => {
        searchInput.value = '';
    });
}

export default clearSearch;
