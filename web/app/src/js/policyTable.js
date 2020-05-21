import {
    getCurrentState,
    getPagination,
    getCounter,
    getData,
    toDisplayOrg,
} from './resultsCommon.js';

const searchFields = [
    'title',
    'text',
    'organisation',
    'authors',
].join(',');

const TITLE_LENGTH = 140;

const getPolicyTableContent = (data) => {
    // Create the table rows to use in the policy-docs result table

    let rows = ``;
    for(let item of data.hits.hits) {
        if (!item._source.doc.url) {
            continue;
        }
        let authors = item._source.doc.authors?item._source.doc.authors:"Unknown";
        let title = (item._source.doc.title)? item._source.doc.title.toTitleCase():"Title unavailable";
        rows += `<tr>`;
        rows += `<td class="new-page-icon-cell"><a
            href="${item._source.doc.url}"
            target="_blank"
            rel="noreferrer noopener"
        ><span class="icn icn-new-page"></span></td>`;
        rows += `<td title="${title}"><a
            href="${item._source.doc.url}"
            target="_blank"
            rel="noreferrer noopener"
        >${(title.length > TITLE_LENGTH) ? (title.slice(0, TITLE_LENGTH) + "...") : title}</a></td>`;
        rows += `<td>${toDisplayOrg(item._source.doc.organisation)}</td>`;
        rows += `<td>${item._source.doc.year?item._source.doc.year:"Unknown"}</td>`;
        rows += `</tr>`;

    }
    return rows;
}


const refreshPolicy = (data, currentState) => {
    // Get the parameters from the policy docs search page and use them
    // to query Elasticsearch

    const table = document.getElementById('policy-docs-results-tbody');
    const loadingRow = document.getElementById('loading-row');
    const pages = document.getElementsByClassName('page-item');

    table.innerHTML = getPolicyTableContent(data);


    table.parentElement.classList.toggle("load");
    loadingRow.classList.toggle("d-none");

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

            document.getElementById('policy-docs-result-table').classList.toggle("load");
            document.getElementById('loading-row').classList.toggle("d-none");

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

                document.getElementById('policy-docs-result-table').classList.toggle("load");
                document.getElementById('loading-row').classList.toggle("d-none");

                currentState.fields = searchFields;
                if (newSort == currentSort.getAttribute('data-sort')) {
                    if (currentSort.getAttribute('data-order') === 'asc') {
                        currentState.order = 'desc';
                        currentSort.setAttribute('data-order', 'desc');

                        currentSort.querySelector('.icn').setAttribute('class', 'icn icn-sorted  icn-sorted-asc');
                    }
                    else {
                        currentState.order = 'asc';
                        currentSort.setAttribute('data-order', 'asc');

                        currentSort.querySelector('.icn').setAttribute('class', 'icn icn-sorted');
                    }
                }

                else {
                    e.currentTarget.setAttribute('data-order', 'asc');

                    currentSort.querySelector('.icn').setAttribute('class', 'icn icn-sort');
                    e.currentTarget.querySelector('.icn').setAttribute('class', 'icn icn-sorted');
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
