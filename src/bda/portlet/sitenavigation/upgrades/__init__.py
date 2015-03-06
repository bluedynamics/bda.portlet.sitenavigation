# -*- coding: utf-8 -*-
from plone.browserlayer.utils import unregister_layer
import logging

logger = logging.getLogger('bda.portlet.sitenavigation upgrade')


def remove_browserlayer(context):
    try:
        unregister_layer(name=u"bda.portlet.sitenavigation")
        logger.info('removed bda.portlet.sitenavigation browser layer')
    except KeyError:
        # No browser layer with name collective.geolocationbehavior registered
        logger.warn('FAILED REMOVING bda.portlet.sitenavigation browser layer')
        pass
