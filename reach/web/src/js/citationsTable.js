import {getCurrentState, getPagination, getCounter, getData} from './resultsCommon.js';

const size = 25;
const searchFields = [
    'match_title',
    'policy_title',
    'organisation',
    'match_source',
    'match_publication',
    'match_authors'
].join(',');

function getCitationsTableContent(data) {
    let rows = ``;
    data.hits.hits.forEach((item) => {
        rows += `<tr class="accordion-row" id="accordion-row-${item._source.doc.reference_id}">`;
        rows += `<td class="accordion-arrow"><i class="icon icon-arrow-down mr-1"></i></td>`
        rows += `<td>${item._source.doc.match_title}</td>`;
        rows += `<td>${item._source.doc.match_publication}</td>`;
        rows += `<td class="authors-cell">${item._source.doc.match_authors}</td>`;
        rows += `<td>${item._source.doc.match_pub_year}</td>`;
        rows += `<td>${item._source.doc.policies.length}</td>`;
        rows += `</tr>`;

        rows += `<tr class="accordion-body hidden" id="accordion-body-${item._source.doc.reference_id}">
                    <td colspan=6 class="accordion-subtable-container">
                    <table class="table accordion-subtable">
                        <tr>
                            <th>Policy Document</th>
                            <th>Policy Organisation</th>
                            <th>Authors</th>
                            <th>Year of Publicaction</th>
                        </tr>
        `;
        item._source.doc.policies.forEach((item) => {
            rows += `<tr>`;
            rows += `<td><a href="${item.source_url}">${item.title}</a></td>`;
            rows += `<td>${item.organisation}</td>`;
            rows += `<td>${item.authors}</td>`;
            rows += `<td>${item.year}</td>`;
        });
        rows += `</table></td>`
        rows += `</tr>`;
    });
    return rows;
}

function refreshCitations(data, currentState) {
    // Get the parameters from the policy docs search page and use them
    // to query Elasticsearch

    const table = document.getElementById('citations-results-tbody');
    const pages = document.getElementsByClassName('page-item');
    const accordions = document.getElementsByClassName('accordion-row');

    table.innerHTML = getCitationsTableContent(data);

    document.getElementById('pagination-box').innerHTML = getPagination(
        currentState.page,
        data,
    );

    document.getElementById('page-counter').innerHTML = getCounter(
        currentState.page,
        data,
    );

    for (let item of pages) {
        item.addEventListener('click', (e) => {
            let currentState = getCurrentState();
            let currentPage = document.getElementById('active-page');
            let pages = document.getElementsByClassName('page-item')
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
            getData('citations', currentState, refreshCitations);
        });
    };

    for (let item of accordions) {
        item.addEventListener('click', (e) => {
            const accordionBodyId = e.currentTarget.getAttribute('id').replace('row', 'body');

            let accordionBody = document.getElementById(accordionBodyId);

            accordionBody.classList.toggle('hidden');
            e.currentTarget.classList.toggle('active-row');
            e.currentTarget.firstChild.firstChild.classList.toggle('icon-arrow-down');
            e.currentTarget.firstChild.firstChild.classList.toggle('icon-arrow-up');
        });
    }
}



const citationsTable = () => {
    const citation_table = document.getElementById('citations-result-table');

    if (citation_table) {
        const headers = document.getElementsByClassName('sort');

        for (let item of headers) {
            item.addEventListener('click', (e) => {
                let newSort = e.currentTarget.getAttribute('data-sort');
                let currentSort = document.getElementById('active-sort');
                let currentState = getCurrentState();

                currentState.fields = searchFields;
                if (newSort === currentState.sort) {
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
                    currentSort.setAttribute('id', null);
                    e.currentTarget.setAttribute('id', 'active-sort');
                }
                currentState.sort = newSort;
                getData('citations', currentState, refreshCitations);
            });
        };

        let body = getCurrentState();
        body.fields = searchFields;
        getData('citations', body, refreshCitations);
    }
}

export default citationsTable;
