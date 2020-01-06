const SIZE = 25;

export function getPagination(currentPage, data) {
	let pages = ``;
	if (currentPage > 0) {
		pages += `<li class="page-item" id="page-previous">Prev</li>`;
	}
	else {
		pages += `<li class="disabled-page-item" id="page-previous">Prev</li>`;
	}

	let maxPages = (data.hits.total.value / SIZE);

	for (let i = 0; i < maxPages; ++i) {
		if (i === currentPage) {
			pages += `<li class="page-item active" id="active-page" data-page="${i}">${i + 1}</li>`;
		}
		else {
			pages += `<li class="page-item" data-page="${i}">${i + 1}</li>`;
		}
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
	currentPage = parseInt(currentPage);
	let currentMin = SIZE * currentPage + 1;
	let currentMax = Math.min(currentMin + SIZE, data.hits.total.value);

	return `<p>${currentMin} to ${currentMax} of ${data.hits.total.value}</p>`;
}

export function getData(type, body, callback) {
	let xhr = new XMLHttpRequest();

	let url = `/api/search/${type}`
		      + `?term=${body.term}`
		      + `&fields=${body.fields}`
		      + `&size=${body.size}`
		      + `&sort=${body.sort}`
		      + `&order=${body.order}`
		      + `&page=${body.page + 1}`;
	console.log(url);
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
	// Get the current values for the search term, order, sorting and page.

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

// const resultsCommon = () => {
// 	const policy_table = document.getElementById('policy-docs-result-table');
// 	const citation_table = document.getElementById('citations-result-table');

// 	let currentPage = document.getElementById('active-page');

// 	if (policy_table) {
// 		let body = getCurrentState();
// 		body.fields = 'text,organisation';
// 		getData('policy-docs', body, refreshPolicy);
// 	}

// 	else if (citation_table) {
// 		let body = getCurrentState();
// 		body.fields = 'Matched title,Extracted title';
// 		getData('policy-docs', body, refreshPolicy);
// 	}

// 	else {
// 		// Do nothing
// 	}
// }
