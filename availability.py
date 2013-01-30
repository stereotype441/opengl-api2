# Dict mapping each API to the minimum version number it supports.
MIN_VERSION = {
    'compatibility': 10,
    'core': 31,
    'gles1': 10,
    'gles2': 20
}

def describe(avail):
    descriptions = []
    for key in sorted(avail.keys()):
        disjunction = avail[key]
        if disjunction == []:
            continue
        descriptions.append(
            '{0}: {1}'.format(key, describe_disjunction(disjunction)))
    if descriptions:
        return ', '.join(descriptions)
    else:
        return 'NEVER'

def describe_disjunction(disjunction):
    if len(disjunction) == 0:
        return 'NEVER'
    elif len(disjunction) == 1:
        return describe_conjunction(disjunction[0], False)
    else:
        return ' OR '.join(
            describe_conjunction(conjunction, True)
            for conjunction in disjunction)

def describe_conjunction(conjunction, parens_needed):
    if len(conjunction) == 0:
        return 'ALWAYS'
    elif len(conjunction) == 1:
        return describe_term(conjunction[0])
    else:
        description = ' AND '.join(describe_term(term) for term in conjunction)
        if parens_needed:
            return '({0})'.format(description)
        else:
            return description

def describe_term(term):
    if term[0] == 'version >=':
        return 'version >= {0}'.format(term[1] / 10.0)
    elif term[0] == 'extension':
        return term[1]
    else:
        raise Exception('Unrecognized term type: {0!r}'.format(term[0]))

def canonicalize(avail):
    result = {}
    for key, disjunction in avail.items():
        result[key] = canonicalize_disjunction(disjunction, MIN_VERSION[key])
    return result

def canonicalize_disjunction(disjunction, min_version):
    disjunction = [canonicalize_conjunction(conjunction, min_version)
                   for conjunction in disjunction]
    # We can now eliminate any conjunction that matches a subset of
    # implementations matched by another conjunction.
    while reduce_disjunction(disjunction):
        pass
    return sorted(disjunction)

def reduce_disjunction(disjunction):
    for i in range(len(disjunction)):
        for j in range(len(disjunction)):
            if i == j:
                continue
            if conjunction_matches_subset(disjunction[i], disjunction[j]):
                # disjunction[i] matches a subset of the
                # implementations matched by disjunction[j], so
                # disjunction[i] is a redundant criterion.
                del disjunction[i]
                return True
    return False

def conjunction_matches_subset(conj1, conj2):
    # For each term in conj2, try to find a term in conj1 that matches
    # a subset of the implementations it matches.  If such a term can
    # be found for all terms in conj2, then conj1 matches a subset of
    # the implementations that conj2 matches.
    for term2 in conj2:
        for term1 in conj1:
            if term_matches_subset(term1, term2):
                break
        else:
            return False
    return True

def canonicalize_conjunction(conjunction, min_version):
    # Discard any terms in the conjunction that are rendered redundant
    # by the fact that the minimum version is min_version.
    conjunction = [
        term for term in conjunction
        if not term_matches_subset(['version >=', min_version], term)]
    # We can eliminate any term that matches a superset of
    # implementations matched by another term.
    while reduce_conjunction(conjunction):
        pass
    return sorted(conjunction)

def reduce_conjunction(conjunction):
    for i in range(len(conjunction)):
        for j in range(len(conjunction)):
            if i == j:
                continue
            if term_matches_subset(conjunction[i], conjunction[j]):
                # conjunction[i] matches a subset of the
                # implementations matched by conjunction[j], so
                # conjunction[j] is a redundant criterion.
                del conjunction[j]
                return True
    return False

def term_matches_subset(term1, term2):
    if term1[0] != term2[0]:
        return False
    if term1[0] == 'version >=':
        return term1[1] >= term2[1]
    elif term1[0] == 'extension':
        return term1[1] == term2[1]
    else:
        raise Exception('Unrecognized term type: {0!r}'.format(term1[0]))

def matches(avail1, avail2, apis = None):
    if apis is None:
        apis = MIN_VERSION.keys()
    for api in apis:
        disjunction1 = avail1.get(
