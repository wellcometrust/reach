import "core-js";
import "core-js/es/array";

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

    // Tracking
    const headerLinks = document.getElementsByClassName('navbar');
    headerLinks.forEach(item => {
      item.addEventListener('click', (e) => {
        if (e.target.tagName == "A") {
          gtag('event', 'Internal click', {
            event_category: 'Header',
            event_label: e.target.innerHTML
          });
        }
      });
    });

    const footerLinks = document.getElementsByTagName('footer');
    footerLinks.forEach(item => {
      item.addEventListener('click', (e) => {
        if (e.target.tagName == "A") {
          gtag('event', 'Internal click', {
            event_category: 'Footer',
            event_label: e.target.innerHTML
          });
        }
      });
    });

    const resultsContactLink = document.getElementById('search-results-contact');
    if (resultsContactLink) {
      resultsContactLink.addEventListener('click', (e) => {
        let source = (e.target.getAttribute('data-from') == "citations")? "Discover citations":"Browse pol docs";
        gtag('event', 'Click', {
          event_category: source,
          event_label: 'Email: search results'
        });
      });
    }
});
