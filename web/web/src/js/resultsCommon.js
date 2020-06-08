const SIZE = 25;

const ORGS = {
    'who_iris': 'WHO IRIS',
    'nice': 'NICE',
    'parliament': 'Parliament',
    'unicef': 'UNICEF',
    'msf': 'MSF',
    'gov_uk': 'Gov.uk',
};

export function toDisplayOrg(org) {
    // Returns an organisation in a display appropriate format.
    return ORGS[org];
}

export function getPagination(currentPage, itemCount) {
    // Create the pagination list relative to the current state

    let pages = ``;
    if (currentPage > 0) {
        pages += `<li class="page-item btn" id="page-previous"><i class="icn icn-chevron-left"></i> Prev</li>`;
    }
    else {
        pages += `<li class="btn disabled-page-item" id="page-previous"><i class="icn icn-chevron-left"></i> Prev</li>`;
    }

    const maxPages = parseInt(Math.ceil(itemCount / SIZE)) - 1;

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
        pages += `<li class="page-item btn" id="page-next">Next  <i class="icn icn-chevron-right"></i></li>`;
    }
    else {
        pages += `<li class="disabled-page-item btn" id="page-next">Next <i class="icn icn-chevron-right"></i></li>`;
    }
    return `<ul class="pages">${pages}</ul>`;

}

export function getCounter(currentPage, itemCount) {
    // Create the results counter (displyed `Docs XX to YY of ZZ`)

    currentPage = parseInt(currentPage);
    let currentMin = SIZE * currentPage + 1;
    let currentMax = Math.min(currentMin + SIZE, itemCount);

    return `<span>Showing ${currentMin} - ${currentMax} of ${itemCount} results</span>`;
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

    const load = setTimeout(() => {
      let table = document.getElementById('citations-result-table');
      if (!table) {
        table = table = document.getElementById('policy-docs-result-table');
      }
      table.classList.add("load");
      document.getElementById('loading-row').classList.remove("d-none");
    }, 2000);

    xhr.onload = () => {
      const loadingRow = document.getElementById('loading-row');

      let table = document.getElementById('citations-result-table');
      if (!table) {
        table = table = document.getElementById('policy-docs-result-table');
      }
      clearTimeout(load);
      if (xhr.status == 200) {
          table.classList.remove("load");
          loadingRow.classList.add("d-none");
          callback(xhr.response, body);
      }
    };

    xhr.onprogress = () => {
    };

    xhr.onabort = () => {
        console.log(xhr.response);
    }

    xhr.onerror = () => {
        console.log(xhr.response);
    };
}

export function getCurrentState(term=null) {
    /* Get the current values for the search term, order, sorting and page and
    return them as a dictionary, used for both refreshing the table and
    query new data through the API. */

    const currentPage = document.getElementById('active-page');
    const currentSort = document.getElementById('active-sort');
    const searchTerm = term ? term : document.getElementById('search-term').value;

    let body = {
        term: searchTerm,
        size: SIZE,
        page: (currentPage) ? parseInt(currentPage.getAttribute('data-page')) : 0,
        sort: currentSort ? currentSort.getAttribute('data-sort') : null,
        order: currentSort ? currentSort.getAttribute('data-order') : 'desc',
    };
    return body;
}
