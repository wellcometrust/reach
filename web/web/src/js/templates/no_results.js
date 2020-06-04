const getNoResultsTemplate = (term, source) => {

  let noResultsTitle = ``;
  let formLabel = ``;
  let formAction = ``;
  let formSubmit = ``;

  if (source == 'policies') {
    noResultsTitle = `Your search for "${term}" in policy&nbspdocuments did not return any results`;
    formLabel = `Search by policy document title, policy organisation or topic`;
    formAction = `/search/policy-docs`;
    formSubmit = `Browse policy documents`;
  } else {
    noResultsTitle = `Your search for "${term}" in citations did not return any results`;
    formLabel = `Search by publication title, journal or year of publication`;
    formAction = `/search/citations`;
    formSubmit = `Discover citations`;
  }

  const template = `
  <div class="container">
    <hr class="hs">
    <div class="columns">
      <div class="column col-8 col-md-12">
        <h1>${noResultsTitle}</h1>
      </div>
    </div>
    <div class="columns">
      <div class="column col-6 col-md-12"></div>
      <div class="column col-6 hide-md"></div>
    </div>
    <div class="columns">
      <hr class="hs">
      <div class="column col-12">
        <p class="form-label">${formLabel}</p>
      </div>
      <div class="column col-6 col-md-12">
        <form action="${formAction}">
          <div class="input-group">
            <input type="text" class="form-input input-xl" placeholder="Search" name="terms" id="search-term" value="${term}">
            <button type="submit" class="btn btn-primary input-group-btn input-btn-xl">${formSubmit}<span class="icn icn-search"></span></button>
          </div>
        </form>
      </div>
      <div class="column col-6 hide-md"></div>
    </div>
    <hr class="fs">
    <div class="columns">
      <div class="column col-6 col-md-12">
        <h3 class="tips-title">Search tips</h3>
        <ul class="tips-list">
          <li>Check your spelling</li>
          <li>Broaden your search by using fewer words or more general terms</li>
          <li>Try searching by topic, area or work or insitute</li>
        </ul>
      </div>
      <div class="column col-6 hide-md"></div>
    </div>
    <hr class="fs">
    <hr class="fs">
      <div class="columns">
        <div class="column col-6 col-md-12">
          <div class="feedback-box">
            <p class="bold">Can't find what you're looking for?</p>
            <p>If something doesn’t look quite right, please get in touch with the team at <a href="mailto:reach@wellcome.ac.uk">reach@wellcome.ac.uk.</a></p>
          </div>
        </div>
      <div class="column col-6 hide-md"></div>
    </div>
  </div>
  <hr class="fs">
  `;

  return template;
};

export default getNoResultsTemplate;
