import pandas as pd
# import numpy as np
import time
import utils
from models import Document, Organisation, Reference, DatabaseEngine
from io import StringIO
from settings import settings


def serialise_matched_reference(data, current_timestamp):
    """Serialise the data matched by the model."""
    serialised_data = {
        'publication_id': data['WT_Ref_Id'],
        'cosine_similarity': data['Cosine_Similarity'],
        'datetime_creation': current_timestamp,
        'document_hash': data['Document id']
    }
    return serialised_data


def serialise_reference(data, current_timestamp):
    """Serialise the data parsed by the model."""
    serialised_data = {
        'author': data.get('Authors'),
        'issue': data.get('Issue'),
        'journal': data.get('Journal'),
        'pub_year': data.get('PubYear'),
        'pagination': data.get('Pagination'),
        'title': data.get('Title'),
        'file_hash': data['Document id'],
        'datetime_creation': current_timestamp,
        'volume': data.get('Volume', None),
    }
    return serialised_data


def save_data(data, name):
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    serialised_data = []
    if name == 'document':
        for d in data:
            serialised_data.append(serialise_reference(data, now))
    else:
        for d in data:
            serialised_data.append(serialise_matched_reference(data, now))

    serialised_dataframe = pd.DataFrame(data)

    serialised_dataframe.drop_duplicates()


def save_to_database(documents, references, session):
    doc_list = documents.where(
        (pd.notnull(documents)),
        None
    ).to_dict(orient='records')
    ref_list = references.where(
        (pd.notnull(references)),
        None
    ).to_dict(orient='records')
    now = time.strftime('%Y-%m-%d %H:%M:%S')

    org = session.query(Organisation).filter(
        Organisation.name == settings.ORGANISATION
    ).first()

    if not org:
        org = Organisation(name=settings.ORGANISATION)
        session.add(org)
    for doc in doc_list:
        serial_doc = serialise_reference(doc, now)
        new_doc = session.query(Document).filter(
            Document.file_hash == serial_doc['file_hash']
            and Document.authors == serial_doc['author']
            and Document.title == serial_doc['title']
        ).first()
        if not new_doc:
            new_doc = Document(
                author=serial_doc['author'],
                issue=serial_doc['issue'],
                journal=serial_doc['journal'],
                volume=serial_doc['volume'],
                pub_year=serial_doc['pub_year'],
                pagination=serial_doc['pagination'],
                title=serial_doc['title'],
                file_hash=serial_doc['file_hash'],
                datetime_creation=serial_doc['datetime_creation'],
                organisation=org,
            )
            session.add(new_doc)
    session.commit()
    for ref in ref_list:
        serial_ref = serialise_matched_reference(ref, now)
        document = session.query(Document).filter(
            Document.file_hash == serial_ref['document_hash']
        ).first()
        new_ref = session.query(Reference).filter(
            Reference.publication_id == serial_ref['publication_id']
            and Reference.id_document == document.id
        ).first()
        if not new_ref:
            new_ref = Reference(
                document=document,
                publication_id=serial_ref['publication_id'],
                cosine_similarity=serial_ref['cosine_similarity'],
                datetime_creation=serial_ref['datetime_creation']
            )
            session.add(new_ref)
    session.commit()


if __name__ == '__main__':
    logger = settings.logger
    logger.info("Reading input files for %s", settings.ORGANISATION)

    file_content = utils.get_file(
        settings.SCRAPER_RESULTS_DIR,
        settings.SCRAPER_RESULTS_FILENAME
    )
    raw_text_data = pd.read_json(file_content, lines=True)

    file_content = utils.get_file(
        settings.REFERENCES_DIR,
        settings.REFERENCES_FILENAME
    )
    csv_file = StringIO(file_content.decode('utf-8'))
    WT_references = pd.read_csv(csv_file)

    mnb = utils.load_pickle_file(
        settings.MODEL_DIR,
        settings.CLASSIFIER_FILENAME
    )
    vectorizer = utils.load_pickle_file(
        settings.MODEL_DIR,
        settings.VECTORIZER_FILENAME
    )

    reference_components = utils.process_reference_section(
        raw_text_data,
        settings.ORGANISATION_REGEX
    )

    t0 = time.time()

    reference_components_predictions = utils.predict_references(
        mnb,
        vectorizer,
        reference_components
    )

    predicted_reference_structures = utils.predict_structure(
        reference_components_predictions,
        settings.PREDICTION_PROBABILITY_THRESHOLD
    )
    predicted_reference_structures['Organisation'] = settings.ORGANISATION

    save_data(predicted_reference_structures, 'document')

    fuzzy_matcher = utils.FuzzyMatcher(
        WT_references,
        settings.FUZZYMATCH_THRESHOLD
    )
    all_match_data = fuzzy_matcher.fuzzy_match_blocks(
        settings.BLOCKSIZE,
        predicted_reference_structures,
        settings.FUZZYMATCH_THRESHOLD
    )

    save_data(all_match_data, 'reference')

    if not settings.DEBUG:
        session = DatabaseEngine.get_session(settings.RDS_URL)
        save_to_database(
            predicted_reference_structures,
            all_match_data,
            session
        )

    t1 = time.time()
    total = t1-t0

    logger.info(
        "Time taken to predict and match for ",
        str(len(reference_components)),
        " is ", str(total)
    )
