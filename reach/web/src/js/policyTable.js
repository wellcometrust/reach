import {
    getCurrentState,
    getPagination,
    getCounter,
    getData
} from './resultsCommon.js';

const searchFields = [
    'title',
    'text',
    'organisation',
    'authors',
].join(',');

const getPolicyTableContent = (data) => {
    // Create the table rows to use in the policy-docs result table

    let rows = ``;
    data.hits.hits.forEach((item) => {
        rows += `<tr>`;
        rows += `<td><a href="${item._source.doc.url}">${item._source.doc.title}</a></td>`;
        rows += `<td>${item._source.doc.organisation}</td>`;
        rows += `<td>${item._source.doc.authors?item._source.doc.authors:"Unknown" }</td>`;
        rows += `<td>${item._source.doc.year?item._source.doc.year:"Unknown"}</td>`;
        rows += `</tr>`;

    });
    return rows;
}


const refreshPolicy = (data, currentState) => {
    // Get the parameters from the policy docs search page and use them
    // to query Elasticsearch

    const table = document.getElementById('policy-docs-results-tbody');
    const pages = document.getElementsByClassName('page-item');

    table.innerHTML = getPolicyTableContent(data);

    for (let htmlElement of document.getElementsByClassName('pagination-box'))
    {
            htmlElement.innerHTML = getPagination(
            currentState.page,
            data,
        );
    }

    for (let htmlElement of document.getElementsByClassName('page-counter'))
    {
            htmlElement.innerHTML = getCounter(
            currentState.page,
            data,
        );
    }

    for (let item of pages) {
        item.addEventListener('click', (e) => {
            let currentState = getCurrentState();
            let currentPage = document.getElementById('active-page');
            let pages = document.getElementsByClassName('page-item');
            currentState.fields = searchFields;
            let newPage = e.currentTarget;

            if (newPage.innerHTML === 'Prev') {
                currentState.page -= 1;
                newPage = pages[currentState.page];
            }

            else if (newPage.innerHTML === 'Next') {
                currentState.page += 1;
                newPage = pages[currentState.page];
            }

            else {
                // newPage is an integer
                currentState.page = parseInt(newPage.getAttribute('data-page'));
            }
            getData('policy-docs', currentState, refreshPolicy);
        });
    };
}

const policyTable = () => {
    const policy_table = document.getElementById('policy-docs-result-table');

    if (policy_table) {
        const headers = document.getElementsByClassName('sort');

        for (let item of headers) {
            item.addEventListener('click', (e) => {
                let newSort = e.currentTarget.getAttribute('data-sort');
                let currentSort = document.getElementById('active-sort');
                let currentState = getCurrentState();

                currentState.fields = searchFields;
                if (newSort == currentSort.getAttribute('data-sort')) {
                    if (currentSort.getAttribute('data-order') === 'asc') {
                        currentState.order = 'desc';
                        currentSort.setAttribute('data-order', 'desc');
                    }
                    else {
                        currentState.order = 'asc';
                        currentSort.setAttribute('data-order', 'asc');
                    }
                }

                else {
                    e.currentTarget.setAttribute('data-order', 'asc');
                }

                currentSort.setAttribute('id', null);
                e.currentTarget.setAttribute('id', 'active-sort');
                currentState.sort = newSort;
                getData('policy-docs', currentState, refreshPolicy);
            });
        };

        let body = getCurrentState();
        body.fields = searchFields;
        getData('policy-docs', body, refreshPolicy);
    }
}

export default policyTable;
