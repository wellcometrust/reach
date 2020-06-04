import clearSearch from './clearSearch.js';
import policyTable from './policyTable.js';
import citationsTable from './citationsTable.js';
import contact from "./v.contact";
import home from './home.js';

document.addEventListener('DOMContentLoaded', function(event) {
    String.prototype.toTitleCase = function() {
        let lower = this.valueOf().toLowerCase();
        return lower.replace(/^\w/, c => c.toUpperCase());;
    };

    clearSearch();
    policyTable();
    citationsTable();
    home();
    contact();
});
