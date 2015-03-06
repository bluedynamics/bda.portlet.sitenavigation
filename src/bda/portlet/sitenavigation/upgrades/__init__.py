# -*- coding: utf-8 -*-
from plone.browserlayer.utils import unregister_layer


def remove_browserlayer(context):
    try:
        unregister_layer(name=u"bda.portlet.sitenavigation")
    except KeyError:
        # No browser layer with name collective.geolocationbehavior registered
        pass
