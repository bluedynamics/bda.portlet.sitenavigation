# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from bda.portlet.sitenavigation import msgFact as _
from plone.app.layout.navigation.interfaces import INavigationQueryBuilder
from plone.app.layout.navigation.interfaces import INavtreeStrategy
from plone.app.layout.navigation.navtree import buildFolderTree
from plone.app.layout.navigation.root import getNavigationRoot
from plone.app.portlets.browser import z3cformhelper
from plone.app.portlets.portlets import navigation as basenav
from plone.memoize import ram
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletRetriever
from plone.portlets.utils import hashPortletInfo
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import field
from zope import schema
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.component import getUtilitiesFor
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
import time


DEFAULT_SEARCH_BASE = 'search_base_context'
SEARCH_BASES = SimpleVocabulary([
    SimpleTerm(
        value='search_base_context',
        title=_('search_base_context', 'Search from current context'),
    ),
    SimpleTerm(
        value='search_base_navroot',
        title=_('search_base_navroot', 'Search from subsite'),
    ),
    SimpleTerm(
        value='search_base_root',
        title=_('search_base_root', 'Search from root portal'),
    ),
])


class ISiteNavigationPortlet(basenav.INavigationPortlet):
    """Schema based on INavigationPortlet + special marker interface.
    """
    root = schema.TextLine(
        title=_(u"label_navigation_root_path", default=u"Root node"),
        description=_(
            u'help_navigation_root',
            default=u"Define the relative path from the portal object to an "
                    "object, which you want to use as search base."
        ),
        required=False,
    )

    search_base = schema.Choice(
        title=_(u"label_search_base", default=u"Search base"),
        description=_(
            u"help_search_base",
            default=u"Select the search base, from where the navtree is "
                    "constructed."),
        vocabulary=SEARCH_BASES,
        default=DEFAULT_SEARCH_BASE,
        required=True
    )

    expand_tree = schema.Bool(
        title=_(u"label_expand_tree", default=u"Expand the Navigation Tree"),
        description=_(
            u"help_expand_tree",
            default=u"Expand the navigation tree for hover navigation, where "
                    "we need the whole tree."),
        default=False,
        required=False
    )

    include_dropdown = schema.Bool(
        title=_(u"label_include_dropdown", default=u"Include Dropdown Menus"),
        description=_(
            u"help_include_dropdown",
            default=u"Defines, if this menu is initialized as dropdown menu"),
        default=False,
        required=False
    )

    css_class_main = schema.Choice(
        title=_(u"label_css_class_main", default=u"Layout"),
        description=_(
            u"help_css_class_main",
            default=u"Sets a different Layout by applying CSS classes."
        ),
        vocabulary="bda.portlet.sitenavigation.Layout",
        required=True
    )

    show_header = schema.Bool(
        title=_(u"label_show_header", default=u"Show Header"),
        description=_(
            u"help_show_header",
            default=u"Show the header with title."),
        default=True,
        required=False
    )

# 1 .. expand the tree from navigation root
# 2 .. search from main portal, unexpanded
# 3 .. search from main portal, with expanded tree


def get_root_path(context, portlet):
    relative_root = portlet.root or ''
    root_path = None
    if portlet.search_base == 'search_base_root':
        portal_url = getToolByName(context, 'portal_url')
        root_path = portal_url.getPortalPath()
    elif portlet.search_base == 'search_base_navroot':
        root_path = getNavigationRoot(context)
    if root_path and relative_root:
        root_path = '{}/{}'.format(
            root_path,
            relative_root.strip('/')
        )
    return root_path


@implementer(INavigationQueryBuilder)
@adapter(Interface, ISiteNavigationPortlet)
class SiteNavtreeQueryBuilder(basenav.QueryBuilder):
    """Query builder with support for expanded navigation structures.
    """

    def __init__(self, context, portlet):
        super(SiteNavtreeQueryBuilder, self).__init__(context, portlet)
        if portlet.search_base == 'search_base_context':
            root_path = self.query['path']['query']
        else:
            root_path = get_root_path(context, portlet)
        if portlet.expand_tree:
            self.query['path'] = {'query': root_path}
        else:
            self.query['path']['query'] = root_path


@implementer(INavtreeStrategy)
@adapter(Interface, ISiteNavigationPortlet)
class SiteNavtreeStrategy(basenav.NavtreeStrategy):
    """Navtree strategy for Site nav with support of mainportal root.
    """

    def __init__(self, context, portlet):
        super(SiteNavtreeStrategy, self).__init__(context, portlet)
        if not portlet.search_base == 'search_base_context':
            self.rootPath = get_root_path(context, portlet)


@implementer(ISiteNavigationPortlet)
class Assignment(basenav.Assignment):
    search_base = DEFAULT_SEARCH_BASE
    expand_tree = False
    include_dropdown = False
    css_class_main = u''
    show_header = True

    def __init__(self, *args, **kwargs):
        if 'search_base' in kwargs:
            self.search_base = kwargs.get('search_base', DEFAULT_SEARCH_BASE)
            del kwargs['search_base']
        if 'expand_tree' in kwargs:
            self.expand_tree = kwargs.get('expand_tree', False)
            del kwargs['expand_tree']
        if 'include_dropdown' in kwargs:
            self.include_dropdown = kwargs.get('include_dropdown', False)
            del kwargs['include_dropdown']
        if 'css_class_main' in kwargs:
            self.css_class_main = kwargs.get('css_class_main', u'')
            del kwargs['css_class_main']
        if 'show_header' in kwargs:
            self.show_header = kwargs.get('show_header', True)
            del kwargs['show_header']
        super(Assignment, self).__init__(*args, **kwargs)


def _render_cachekey(method, self):
    # portlethash = hash(self.data)
    portlethash = self.portlethash
    # if self.expand_tree and self.search_base is not 'search_base_context':
    #     # cannot cache on root, as long as selected class is set on template
    #     path = get_root_path(self.context, self)
    path = '/'.join(self.context.getPhysicalPath())
    portal_membership = getToolByName(self.context, 'portal_membership')
    timeout = time.time() // (60 * 60)  # cache for 60 min
    cachekey = (
        portlethash,
        path,
        portal_membership.getAuthenticatedMember().id,
        timeout
    )
    return cachekey


class Renderer(basenav.Renderer):

    @property
    def search_base(self):
        return getattr(self.data, 'search_base', DEFAULT_SEARCH_BASE)

    @property
    def expand_tree(self):
        return getattr(self.data, 'expand_tree', False)

    @property
    def include_dropdown(self):
        return getattr(self.data, 'include_dropdown', False)

    @property
    def css_class_main(self):
        return getattr(self.data, 'css_class_main', u'')

    @property
    def show_header(self):
        return getattr(self.data, 'show_header', True)

    @ram.cache(_render_cachekey)
    def getNavTree(self, _marker=None):
        if _marker is None:
            _marker = []
        context = aq_inner(self.context)
        queryBuilder = getMultiAdapter(
            (context, self.data),
            INavigationQueryBuilder
        )
        strategy = getMultiAdapter((context, self.data), INavtreeStrategy)

        return buildFolderTree(
            context,
            obj=context,
            query=queryBuilder(),
            strategy=strategy
        )

    @property
    def portlethash(self):
        portlethash = None
        assignment = aq_base(self.data)

        # Get the portlet info, to get the portlet hash.
        # THIS IS CRAZY!
        context = self.context
        for name, manager in getUtilitiesFor(IPortletManager, context=context):
            retriever = getMultiAdapter((context, manager), IPortletRetriever)
            portlets = retriever.getPortlets()
            for portlet in portlets:
                if assignment == portlet['assignment']:
                    # got you
                    portlet['manager'] = self.manager.__name__  # not available in portlet info, yet. hurray.  # noqa
                    portlethash = hashPortletInfo(portlet)
        return portlethash

    @ram.cache(_render_cachekey)
    def render(self):
        return self._template()

    _template = ViewPageTemplateFile('sitenavigation.pt')
    recurse = ViewPageTemplateFile('sitenavigation_recurse.pt')


class AddForm(z3cformhelper.AddForm):
    fields = field.Fields(ISiteNavigationPortlet)
    label = _(u"Add Site Navigation Portlet")
    description = _(u"Shows a site navigation tree.")

    def create(self, data):
        return Assignment(**data)


class EditForm(z3cformhelper.EditForm):
    fields = field.Fields(ISiteNavigationPortlet)
    label = _(u"Edit Site Navigation Portlet")
    description = _(u"Shows a site navigation tree.")
