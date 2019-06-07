# -*- coding: utf-8 -*-

import dill
import re

from sklearn.pipeline import Pipeline

def split_section(references_section, model):

    lines = references_section.split('\n')

    line_beginnings = [m.start() for m in re.finditer(r"\n", references_section)]
    if references_section[0] != "\n":
        line_beginnings = [0] + line_beginnings

    predict_tags = model.predict(lines)
    prob_tags = [p.max() for p in model.predict_proba(lines)]

    # Cut up references_section at the line beginning of a line predicted to be a B
    cut_here = [wb for (wb, t, p) in zip(line_beginnings, predict_tags, prob_tags) if t == "B"]

    # Cut references_section at each index in cut_here:
    references = [references_section[i:j] for i,j in zip(cut_here, cut_here[1:] + [None])]

    return references
