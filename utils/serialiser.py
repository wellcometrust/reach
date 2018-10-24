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
    if data.get('Title'):
        title = data['Title'][:1024]
    else:
        title = None

    for key, value in data.items():
        if value and key != 'Title' and type(value) == str:
            data[key] = value[:256]

    if type(data['PubYear']) != int:
        data['PubYear'] = None

    serialised_data = {
        'author': data.get('Authors'),
        'issue': data.get('Issue'),
        'journal': data.get('Journal'),
        'pub_year': data.get('PubYear'),
        'pagination': data.get('Pagination'),
        'title': title,
        'file_hash': data['Document id'],
        'datetime_creation': current_timestamp,
        'volume': data.get('Volume', None),
    }
    return serialised_data
