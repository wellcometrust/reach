const SIZE = 25;

export function getPagination(currentPage, data) {
    // Create the pagination list relative to the current state

    let pages = ``;
    if (currentPage > 0) {
        pages += `<li class="page-item" id="page-previous">Prev</li>`;
    }
    else {
        pages += `<li class="disabled-page-item" id="page-previous">Prev</li>`;
    }

    const maxPages = (data.hits.total.value / SIZE);

    if (currentPage > 2) {
        pages += `<li class="page-item" data-page="0">1</li>`;

        if (currentPage > 3) {
            pages += `<li class="disabled-page-item">...</li>`;
        }
    }

    for (let i = Math.max(currentPage - 2, 0); i < Math.min(currentPage + 3, maxPages); ++i) {
        if (i === currentPage) {
            pages += `<li class="page-item active" id="active-page" data-page="${i}">${i + 1}</li>`;
        }
        else {
            pages += `<li class="page-item" data-page="${i}">${i + 1}</li>`;
        }
    }



    if (currentPage < maxPages - 3) {

        if (currentPage < maxPages - 4) {
            pages += `<li class="disabled-page-item">...</li>`;
        }

        pages += `<li class="page-item" data-page="${maxPages - 1}">${maxPages}</li>`;
    }

    if (currentPage < maxPages - 1) {
        pages += `<li class="page-item" id="page-next">Next</li>`;
    }
    else {
        pages += `<li class="disabled-page-item" id="page-next">Next</li>`;
    }
    return `<ul class="pagination">${pages}</ul>`;

}

export function getCounter(currentPage, data) {
    // Create the results counter (displyed `Docs XX to YY of ZZ`)

    currentPage = parseInt(currentPage);
    let currentMin = SIZE * currentPage + 1;
    let currentMax = Math.min(currentMin + SIZE, data.hits.total.value);

    return `<p>${currentMin} to ${currentMax} of ${data.hits.total.value}</p>`;
}

export function getData(type, body, callback) {
    /* Query Reach public API to get the table data and callback
      a refresh on that table.

    Args:
        type: the type of the data to get, passed as a string.
              Should be either `policy-docs` or `citations`

        body: a dictionary containing the current state of the
              table

        callback: the table refresh function to call when this
                  function received data
    */

    let xhr = new XMLHttpRequest();

    let url = `/api/search/${type}`
              + `?terms=${body.term}`
              + `&fields=${body.fields}`
              + `&size=${body.size}`
              + `&sort=${body.sort}`
              + `&order=${body.order}`
              + `&page=${body.page + 1}`;

    xhr.open('GET', url);
    xhr.responseType = 'json';
    xhr.send();

    xhr.onload = () => {
        if (xhr.status == 200) {
            callback(xhr.response, body);
        }
    };

    xhr.onabort = () => {
        console.log(xhr.response);
    }

    xhr.onerror = () => {
        console.log(xhr.response);
    };
}

export function getCurrentState() {
    /* Get the current values for the search term, order, sorting and page and
    return them as a dictionary, used for both refreshing the table and
    query new data through the API. */

    const currentPage = document.getElementById('active-page');
    const currentSort = document.getElementById('active-sort');
    const searchTerm = document.getElementById('search-term');

    let body = {
        term: searchTerm.value,
        size: SIZE,
        page: (currentPage) ? parseInt(currentPage.getAttribute('data-page')) : 0,
        sort: currentSort.getAttribute('data-sort'),
        order: currentSort.getAttribute('data-order'),
    };
    return body;
}
