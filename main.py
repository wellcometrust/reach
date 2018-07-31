import pandas as pd
import numpy as np
import time
import pickle
from models import Document, Organisation, Reference, DatabaseEngine
from separate import process_reference_section
from predict import predict_references, predict_structure
from fuzzymatch import FuzzyMatcher
from s3 import S3
from io import StringIO
from settings import settings


def get_file_key(file_path, file_name):
    return "/".join([file_path, file_name])


def get_file_content(file_path, file_name=None, file_format='json'):
    if file_name:
        file_key = get_file_key(file_path, file_name)

    if settings.BUCKET:
        s3 = S3(settings.BUCKET)
        if not file_name:
            file_key = s3._get_last_modified_file_key(file_path)
        file_content = s3.get(file_key)
        if file_format == 'csv':
            file_content = file_content.decode('utf-8')
    else:
        file_mode = 'rb' if 'pkl' in file_name else 'r'
        file_content = open(file_key, file_mode).read()

    return file_content


def load_data_file(file_path, file_name=None, file_format='json'):
    file_content = get_file_content(file_path, file_name, file_format)
    if file_format == 'csv':
        file = StringIO(file_content)
        raw_text_data = pd.read_csv(file)
    else:
        raw_text_data = pd.read_json(file_content, lines=True)
    return raw_text_data


def load_pickle_file(file_path, file_name):
    file_content = get_file_content(file_path, file_name)
    unpickled_file = pickle.loads(file_content)
    return unpickled_file


def serialise_matched_reference(data, current_timestamp):
    serialised_data = {
        'publication_id': data['WT_Ref_Id'],
        'cosine_similarity': data['Cosine_Similarity'],
        'datetime_creation': current_timestamp,
        'document_hash': data['Document id']
    }
    return serialised_data


def serialise_reference(data, current_timestamp):
    serialised_data = {
        'author': data.get('Authors'),
        'issue': data.get('Issue', ''),
        'journal': data.get('Journal'),
        'pub_year': data.get('PubYear', ''),
        'pagination': data.get('Pagination', ''),
        'title': str(data.get('Title'))[:1024],
        'file_hash': data['Document id'],
        'datetime_creation': current_timestamp,
        'volume': data.get('Volume', None),
    }
    return serialised_data


def get_number(item):
    if isinstance(item, int):
        return item
    if isinstance(item, str):
        ints = [int(s) for s in str.split(' ') if s.isdigit()]
        if ints:
            return ints[0]
    return None


def get_clean_str(item):
    if item is np.nan:
        return ''
    else:
        return item


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
    doc_list = documents.to_dict(orient='records')
    ref_list = references.to_dict(orient='records')
    now = time.strftime('%Y-%m-%d %H:%M:%S')

    org = session.query(Organisation).filter(
        Organisation.name == settings.organisation
    ).first()

    if not org:
        org = Organisation(name=settings.organisation)
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
                author=get_clean_str(serial_doc['author']),
                issue=get_clean_str(serial_doc['issue']),
                journal=get_clean_str(serial_doc['journal']),
                volume=get_clean_str(serial_doc['volume']),
                pub_year=get_number(serial_doc['pub_year']),
                pagination=get_clean_str(serial_doc['pagination']),
                title=get_clean_str(serial_doc['title']),
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
    # ============================
    # All external files:
    # ============================
    print("Reading input files for {}... ".format(settings.organisation))

    # Unstructured references from latest policy scrape:
    raw_text_data = load_data_file(
        settings.raw_text_prefix,
        settings.raw_text_file_name
    )

    # Import all the funder = 'WT' publications from all time:
    WT_references = load_data_file(
        settings.wt_references_prefix,
        settings.wt_references_file_name,
        'csv'
    )

    # ============================
    # Load trained model  ========
    mnb = load_pickle_file(
        settings.model_prefix,
        settings.classifier_file_name
    )
    vectorizer = load_pickle_file(
        settings.model_prefix,
        settings.vectorizer_file_name
    )

    # ============================
    # Separate ===================

    # Separate out the references and reference components from the raw text

    reference_components = process_reference_section(
        raw_text_data,
        settings.organisation_regex
    )

    # ============================
    # Predict ====================

    # Use the model to predict the category for each reference component,
    # then structure

    # Just a sample for now!

    t0 = time.time()

    reference_components_predictions = predict_references(
        mnb,
        vectorizer,
        reference_components
    )

    # Structure:
    predicted_reference_structures = predict_structure(
        reference_components_predictions,
        settings.prediction_probability_threshold
    )
    predicted_reference_structures['Organisation'] = settings.organisation

    save_data(predicted_reference_structures, 'document')

    # ============================
    # Match ======================

    # Fuzzy match the newly structured references with the list of WT funded
    # publications found in Dimensions

    fuzzy_matcher = FuzzyMatcher(
        WT_references,
        settings.fuzzymatch_threshold
    )
    all_match_data = fuzzy_matcher.fuzzy_match_blocks(
        settings.blocksize,
        predicted_reference_structures,
        settings.fuzzymatch_threshold
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

    print(
        "Time taken to predict and match for ",
        str(len(reference_components)),
        " is ", str(total)
    )
