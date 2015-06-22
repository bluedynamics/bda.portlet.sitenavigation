# -*- coding: utf-8 -*-
from bda.portlet.sitenavigation import msgFact as _
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@provider(IVocabularyFactory)
def Layout(context):
    """Sitenavigation Layout Vocabulary.

    Sets the main CSS classes of the initial ``ul`` node.

    Override via overrides.zcml to fit your project's needs.
    """
    items = [
        (_('latout_none', default="No special layout"), ''),
        (_('layout_bootstrap_standard', default="Standard Bootstrap"), 'nav'),
    ]
    items = [SimpleTerm(title=i[0], value=i[1]) for i in items]
    return SimpleVocabulary(items)
