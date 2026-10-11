"""Keep synthetic rule agreement separate from independent observed validation."""


def reference_scope(rows, independent_field, source_field):
    if not rows:
        raise ValueError('Reference rows are required')
    kinds = set()
    for row in rows:
        if not row.get(source_field):
            raise ValueError('Every label requires a documented reference source')
        kind = row.get('reference_kind')
        if kind in ('documented_rule', 'simulator'):
            if not row.get('label_methodology'):
                raise ValueError('Synthetic reference labels require explicit label_methodology')
        elif kind in (None, 'observed') and row.get(independent_field) is True:
            kind = 'independent_reference'
        else:
            raise ValueError('Independent reference review or documented synthetic label methodology required')
        kinds.add(kind)
    return {'reference_kinds': sorted(kinds),
            'scope': 'independent reference validation' if kinds == {'independent_reference'} else 'synthetic/reference agreement',
            'limitation': None if kinds == {'independent_reference'} else
                'Rule/simulator label agreement does not establish measured real-world accuracy.'}
