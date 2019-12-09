
async function searchES(type, body) {
	let xhr = new XMLHttpRequest();

	let url = `/api/search/${type}`
		      + `?term=${body.term}`
		      + `&fields=${body.fields}`
		      + `&size=${body.size}`
		      + `&sort=${body.sort}`
		      + `&page=${body.page}`;
		xhr.open('GET', url);
		xhr.responseType = 'json';
		xhr.send();

		xhr.onload = () => {
			if (xhr.status == 200) {
				console.log(xhr.response);
			}
		}
}

function searchCitations(citation_table) {
	// Get the parameters from the citation search page and use them
	// to query Elasticsearch
	citation_table.addEventListener('click', () => {
		const body = {
			fields: 'Extracted title',
			term: 'malaria',
			size: 25,
			page: 1,
			sort: 'text'
		}

		response = await searchES('policy-docs', body);
	});
}

function searchPolicy(policy_table) {
	// Get the parameters from the policy docs search page and use them
	// to query Elasticsearch
	policy_table.addEventListener('click', () => {
		const body = {
			fields: 'text,organisation',
			term: 'malaria',
			size: 25,
			page: 1,
			sort: 'text'
		}

		response = await searchES('policy-docs', body);
	});
}

const elasticCommon = () => {
	const policy_table = document.getElementById('policy-docs-result-table');
	const citation_table = document.getElementById('citations-result-table');

	if (policy_table) {
		console.log('policy docs page');
		searchPolicy(policy_table);
	}

	else if (citation_table) {
		console.log('citation page');
	}

	else {
		// Do nothing
	}
}

export default elasticCommon
