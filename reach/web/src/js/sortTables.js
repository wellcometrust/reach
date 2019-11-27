const List = require('list.js');

function updateCount(htmlItem) {
    let current = 1;
    let trs = document.getElementsByTagName('tr');
    let resultCountDiv = document.getElementById('result-count');
    let maxEsResults = document.getElementById('max-results');
    if (!maxEsResults) {
    	return null;
    } else {
    	maxEsResults = parseInt(maxEsResults.innerText);
    }


    if (htmlItem && htmlItem.innerText) {
        current = parseInt(htmlItem.innerText);
    }

    let maxResults = (maxEsResults < 25 || (25 + (current - 1) * 25) > maxEsResults)? maxEsResults : 25 + (current - 1) * 25;
    let resultsTemplate = `${1 + (current - 1) * 25} - ${maxResults} of `;

    resultCountDiv.innerText = resultsTemplate;
}

const sortTables = (reach) => {
    var policyTable = new List('policy-docs-result-table', {
          valueNames: ['pub-name', 'organisation', 'authors', 'year'],
          page: 25,
          innerWindow: 3,
          outerWindow: 3,
          pagination: true,
    });


    var citationTable = new List('citations-result-table', {
          valueNames: ['pub-name', 'organisation', 'authors', 'year'],
          page: 25,
          innerWindow: 3,
          outerWindow: 3,
          pagination: true,
    });

    updateCount(false);

    let pageLink = document.getElementsByClassName('pagination');
    if (pageLink.length === 0) {
    	return null;
    }
    pageLink[0].addEventListener('click', function(event) {
        updateCount(event.target);
    });
};

export default sortTables;
