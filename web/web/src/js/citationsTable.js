import {
    getCurrentState,
    getPagination,
    getCounter,
    getData,
    toDisplayOrg,
} from './resultsCommon.js';

import getNoResultsTemplate from './templates/no_results.js';

const TITLE_LENGTH = 140;

const searchFields = [
    'match_title',
    'policies.title',
    'policies.organisation',
    'match_source',
    'match_publication',
    'match_authors'
].join(',');

function getCitationsTableContent(data) {
    let rows = ``;
    for (let item of data) {
      let authors = [];
      for (let author of  item.authors) {
        authors.push(Object.values(author).join('. '));
      }
      let match_title = item.title ? item.title.toTitleCase() : "Title unavailable";

      if (item.policies) {
        rows += `<tr class="accordion-row" id="accordion-row-${item.uuid}">`;
      } else {
        rows += `<tr class="empty-accordion-row" id="accordion-row-${item.uuid}">`;
      }
      rows += `<td class="accordion-arrow"><i class="icon icon-arrow-down mr-1"></i></td>`
      rows += `<td title="${match_title}"><div>${match_title}</div></td>`;
      rows += `<td>${item.journal_title}</td>`;
      rows += `<td class="authors-cell" title="${authors.join(' ')}"><div>
          ${authors.join(' ')}</div>
      </td>`;
      rows += `<td>${item.pub_year}</td>`;

      if (item.policies) {
        rows += `<td>${item.policies.length}</td>`;
        rows += `</tr>`;

        rows += `<tr class="accordion-body fadeout" id="accordion-body-${item.uuid}">
                    <td></td>
                    <td colspan=4 class="accordion-subtable-container"><div>
                    <table class="table accordion-subtable">
                        <colgroup>
                            <col class="colgroup-accordion-col">
                            <col class="colgroup-subtable-col">
                            <col class="colgroup-medium-col">
                            <col>
                        </colgroup>
                        <tr>
                            <th colspan="2">Cited in the following Policy Documents</th>
                            <th>Policy Organisation</th>
                            <th>Publication Year</th>
                        </tr>
        `;
        for (let policy of item.policies) {
            let policy_title = policy.title ? policy.title.toTitleCase() : "Title unavailable";
            rows += `<tr>`;
            rows += `<td><span class="icn icn-new-page"></span></td>`
            rows += `<td title="${policy_title}"><a
               href="${policy.source_url}"
               target="_blank"
               rel="noreferrer noopener"
               class="associated-policy-a"
            >${(policy_title.length > TITLE_LENGTH) ? (policy_title.slice(0, TITLE_LENGTH) + "...") : policy_title}</a></td>`;
            rows += `<td>${toDisplayOrg(policy.source_org)}</td>`;
            rows += `<td>${policy.year}</td>`;
        }
        rows += `</table></div></td>`
        rows += `</tr>`;

      }
      else {
        rows += `<td>0</td>`;
        rows += `<tr class="accordion-body fadeout" id="accordion-body-${item.uuid}">
                    <td></td>
                    <td colspan=4 class="accordion-subtable-container"><div></div></td>
                 </tr>`;
      }
    }
    return rows;
}

function refreshCitationsSortIcons(data, currentState) {
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

      if (currentSort) {
        currentSort.setAttribute('id', null);
        currentSort.querySelector('.icn').setAttribute('class', 'icn icn-sort');
      }
      currentState.newSortTarget.setAttribute('id', 'active-sort');
      currentState.newSortTarget.querySelector('.icn').setAttribute('class', 'icn icn-sorted');

  }

  refreshCitations(data, currentState);
}

function refreshCitations(data, currentState) {
    // Get the parameters from the policy docs search page and use them
    // to query Elasticsearch

    const resultBox = document.getElementById('citations-results');
    const table = document.getElementById('citations-results-tbody');
    // const loadingRow = document.getElementById('loading-row');
    const pages = document.getElementsByClassName('page-item');

    if (parseInt(data.count) <= 0) {
      resultBox.innerHTML = getNoResultsTemplate(data.terms, 'citations');

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

    table.innerHTML = getCitationsTableContent(data.data);

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
            e.preventDefault();
            let currentState = getCurrentState();
            let currentPage = document.getElementById('active-page');
            let pages = document.getElementsByClassName('page-item')
            currentState.fields = searchFields;

             let newPage = e.currentTarget;

            if (newPage.getAttribute('id') == 'page-previous') {
                currentState.page -= 1;
                newPage = pages[currentState.page];
                gtag('event', 'Pagination click', {
                  event_category: 'Discover citations',
                  event_label: 'Prev'
                });
            }

            else if (newPage.getAttribute('id') == 'page-next') {
                currentState.page += 1;
                newPage = pages[currentState.page];
                gtag('event', 'Pagination click', {
                  event_category: 'Discover citations',
                  event_label: 'Next'
                });
            }

            else {
                // newPage is an integer
                currentState.page = parseInt(newPage.getAttribute('data-page'));
                gtag('event', 'Pagination click', {
                  event_category: 'Discover citations',
                  event_label: newPage.getAttribute('data-page')
                });
            }
            getData('citations', currentState, refreshCitations);
        });
    };

    const accordions = document.getElementsByClassName('accordion-row');

    for (let item of accordions) {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopImmediatePropagation();

        gtag('event', 'Click', {
          event_category: 'Discover citations',
          event_label: 'Accordion'
        });

        const foldOnly = e.currentTarget.classList.contains('active-row');

        // Disable other active rows
        let activeRows = document.getElementsByClassName('active-row');
        for (let row of activeRows) {
          row.classList.toggle('active-row');
          row.firstChild.firstChild.classList.toggle('icn-up');
          let accordionBodyId = row.getAttribute('id').replace('row', 'body');
          let accordionBody = document.getElementById(accordionBodyId);
          accordionBody.classList.toggle('fadein');
          accordionBody.classList.toggle('fadeout');
        }

        if (!foldOnly) {
          // Enable Actual active row
          let accordionBodyId = e.currentTarget.getAttribute('id').replace('row', 'body');
          let accordionBody = document.getElementById(accordionBodyId);

          accordionBody.classList.toggle('fadein');
          accordionBody.classList.toggle('fadeout');
          e.currentTarget.classList.toggle('active-row');
          e.currentTarget.firstChild.firstChild.classList.toggle('icn-up');
        }
      });
    }

    const policyLinks = document.getElementsByClassName('associated-policy-a');

    for (let item of policyLinks) {
      item.addEventListener('click', () => {
        gtag('event', 'Click', {
          event_category: 'Discover citations',
          event_label: 'Pol doc link'
        });
      });
    }
}



const citationsTable = () => {
    const resultBox = document.getElementById('citations-results');

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
                event_category: 'Discover citations',
                event_label: newSort
              });
              getData('citations', currentState, refreshCitationsSortIcons);
          });
      };

      let csvButton = document.getElementById('csv-download-button');
      let searchTerm = resultBox.getAttribute('data-search');

      csvButton.addEventListener('click', (e) => {
        gtag('event', 'Download', {
          event_category: 'Discover citations',
          event_label: 'CSV_' + searchTerm
        });
      });

      let body = getCurrentState(searchTerm);
      body.fields = searchFields;
      gtag('event', 'Search', {
        event_category: 'Discover citations',
        event_label: searchTerm
      });
      getData('citations', body, refreshCitations);
    }
}

export default citationsTable;
