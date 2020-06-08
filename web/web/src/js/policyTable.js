import {
    getCurrentState,
    getPagination,
    getCounter,
    getData,
    toDisplayOrg,
} from './resultsCommon.js';

import getNoResultsTemplate from './templates/no_results.js';

const searchFields = [
    'title',
    'source_org',
    'authors',
].join(',');

const TITLE_LENGTH = 140;

const getPolicyTableContent = (data) => {
    // Create the table rows to use in the policy-docs result table

    let rows = ``;
    for(let item of data) {
        if (!item.source_doc_url) {
            continue;
        }
        let title = (item.title)? item.title.toTitleCase():"Title unavailable";
        rows += `<tr>`;
        rows += `<td class="new-page-icon-cell"><a
            href="${item.source_doc_url}"
            target="_blank"
            rel="noreferrer noopener"
        ><span class="icn icn-new-page"></span></td>`;
        rows += `<td title="${title}"><a
            href="${item.source_doc_url}"
            target="_blank"
            rel="noreferrer noopener"
        >${(title.length > TITLE_LENGTH) ? (title.slice(0, TITLE_LENGTH) + "...") : title}</a></td>`;
        rows += `<td>${toDisplayOrg(item.source_org)}</td>`;
        rows += `<td>${item.year ? item.year : "Unknown"}</td>`;
        rows += `</tr>`;

    }
    return rows;
}


const refreshPolicy = (data, currentState) => {
    // Get the parameters from the policy docs search page and use them
    // to query Elasticsearch
    const resultBox = document.getElementById('policy-docs-results');
    const table = document.getElementById('policy-docs-results-tbody');
    // const loadingRow = document.getElementById('loading-row');
    const pages = document.getElementsByClassName('page-item');

    if (parseInt(data.count) <= 0) {
      resultBox.innerHTML = getNoResultsTemplate(data.terms, 'policies');
      return null;
    }

    table.innerHTML = getPolicyTableContent(data.data);

    for (let htmlElement of document.getElementsByClassName('pagination-box'))
    {
      htmlElement.innerHTML = getPagination(
        currentState.page,
        parseInt(data.count),
      );
    }

    for (let htmlElement of document.getElementsByClassName('page-counter'))
    {
      htmlElement.innerHTML = getCounter(
          currentState.page,
          parseInt(data.count),
      );
    }

    for (let item of pages) {
        item.addEventListener('click', (e) => {
            let currentState = getCurrentState();
            let currentPage = document.getElementById('active-page');
            let pages = document.getElementsByClassName('page-item');

            currentState.fields = searchFields;
            let newPage = e.currentTarget;

            if (newPage.getAttribute('id') == 'page-previous') {
                currentState.page -= 1;
                newPage = pages[currentState.page];
            }

            else if (newPage.getAttribute('id') == 'page-next') {
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
}

const policyTable = () => {
    const resultBox = document.getElementById('policy-docs-results');

    if (resultBox) {
        let body = getCurrentState(resultBox.getAttribute('data-search'));
        body.fields = searchFields;
        getData('policy-docs', body, refreshPolicy);
    }
}

export default policyTable;
