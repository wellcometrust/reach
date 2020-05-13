import datetime
import re

from refparse.settings import settings


def structure_reference(reference_components):
    """
    Join up all the predictions for each component type into one string
    TO DO: Evaluate how often the same component type is predicted
        but not next to one another.
        e.g. ref_components = ['title', 'title', 'year', 'title']
    """

    ref_tokens = [r[0] for r in reference_components]
    ref_components = [r[1] for r in reference_components]

    # Keep empty strings for classes not predicted from the deep reference parser
    # Useful for possible downstream errors
    structured_reference = {ref_class: '' for ref_class in settings.REF_CLASSES}
    for component in settings.DRP_REF_COMPONENTS:
        # Leave component name unchanged if no map
        structured_reference[
            settings.COMPONENT_NAME_MAP.get(component, component)
            ] = ' '.join([r[0] for r in reference_components if r[1]==component])

    return structured_reference