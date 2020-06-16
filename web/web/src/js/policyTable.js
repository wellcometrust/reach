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


function refreshPolicySortIcons(data, currentState) {
  let newSort = currentState.newSortTarget.getAttribute('data-sort');
  let currentSort = document.getElementById('active-sort');

  currentState.fields = searchFields;
  if (currentState.sort === currentState.lastSort) {
      if (currentSort.getAttribute('data-order') === 'asc') {
          currentState.order = 'desc';
          currentSort.setAttribute('data-order', 'desc');

          currentSort.querySelector('.icn').setAttribute('class', 'icn icn-sorted icn-sorted-asc');
      }
      else {
          currentState.order = 'asc';

          if (currentSort) {
          currentSort.setAttribute('data-order', 'asc');
          currentSort.querySelector('.icn').setAttribute('class', 'icn icn-sorted');
          }
      }
  }

  else {
      currentState.newSortTarget.setAttribute('data-order', 'asc');

      if (currentSort){
        currentSort.setAttribute('id', null);
        currentSort.querySelector('.icn').setAttribute('class', 'icn icn-sort');
      }

      currentState.newSortTarget.setAttribute('id', 'active-sort');
      currentState.newSortTarget.querySelector('.icn').setAttribute('class', 'icn icn-sorted');

  }

  refreshPolicy(data, currentState);
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


      const noResultContactLink = document.getElementById('no-results-contact');
      if (noResultContactLink) {
        noResultContactLink.addEventListener('click', (e) => {
          let source = (e.target.getAttribute('data-from') == "citations")? "Discover citations":"Browse pol docs";
          gtag('event', 'Click', {
            event_category: source,
            event_label: 'Email no results'
          });
        });
      }

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
                gtag('event', 'Pagination click', {
                  event_category: 'Browse pol docs',
                  event_label: 'Prev'
                });
            }

            else if (newPage.getAttribute('id') == 'page-next') {
                currentState.page += 1;
                newPage = pages[currentState.page];
                gtag('event', 'Pagination click', {
                  event_category: 'Browse pol docs',
                  event_label: 'Next'
                });
            }

            else {
                // newPage is an integer
                currentState.page = parseInt(newPage.getAttribute('data-page'));
                gtag('event', 'Pagination click', {
                  event_category: 'Browse pol docs',
                  event_label: newPage.getAttribute('data-page')
                });
            }
            getData('policy-docs', currentState, refreshPolicy);
        });
    };
}

const policyTable = () => {
    const resultBox = document.getElementById('policy-docs-results');

    if (resultBox) {
      const headers = document.getElementsByClassName('sort');

      for (let item of headers) {
          item.addEventListener('click', (e) => {
              e.preventDefault();
              e.stopImmediatePropagation();

              let newSort = e.currentTarget.getAttribute('data-sort');
              let currentSort = document.getElementById('active-sort');
              let currentState = getCurrentState();

              currentState.fields = searchFields;
              if (newSort === currentState.sort) {
                  if (currentSort.getAttribute('data-order') === 'asc') {
                      currentState.order = 'desc';
                  }
                  else {
                      currentState.order = 'asc';
                  }
              } else {
                currentState.order = 'asc';
              }

              currentState.lastSort = currentState.sort;
              currentState.newSortTarget = e.currentTarget;
              currentState.sort = newSort;
              gtag('event', 'Sort', {
                event_category: 'Browse pol docs',
                event_label: newSort
              });
              getData('policy-docs', currentState, refreshPolicySortIcons);
          });
      };

      let csvButton = document.getElementById('csv-download-button');
      let searchTerm = resultBox.getAttribute('data-search')

      csvButton.addEventListener('click', (e) => {
        gtag('event', 'Download', {
          event_category: 'Browse pol docs',
          event_label: 'CSV_' + searchTerm
        });
      });

      let body = getCurrentState(searchTerm);
      body.fields = searchFields;

      gtag('event', 'Search', {
        event_category: 'Browse pol docs',
        event_label: searchTerm
      });
      getData('policy-docs', body, refreshPolicy);
    }
}

export default policyTable;
