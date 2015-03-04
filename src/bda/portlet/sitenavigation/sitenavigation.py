from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bda.portlet.sitenavigation import msgFact as _
from plone.app.layout.navigation.interfaces import INavigationQueryBuilder
from plone.app.layout.navigation.interfaces import INavtreeStrategy
from plone.app.layout.navigation.navtree import buildFolderTree
from plone.app.layout.navigation.root import getNavigationRoot
from plone.app.portlets.portlets import base
from plone.app.portlets.portlets import navigation as basenav
from plone.memoize.instance import memoize
from zope import schema
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.formlib import form
from zope.interface import Interface
from zope.interface import implements
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


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
        required=False
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

    css_class_main = schema.TextLine(
        title=_(u"label_css_class_main", default=u"Main CSS classes"),
        description=_(u"help_css_class_main",
                      default=u"Space seperated list of wrapper css classes"),
        default=u"",
        required=False
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


class SiteNavtreeQueryBuilder(basenav.QueryBuilder):
    """Query builder with support for expanded navigation structures.
    """
    implements(INavigationQueryBuilder)
    adapts(Interface, ISiteNavigationPortlet)

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


class SiteNavtreeStrategy(basenav.NavtreeStrategy):
    """Navtree strategy for Site nav with support of mainportal root.
    """
    implements(INavtreeStrategy)
    adapts(Interface, ISiteNavigationPortlet)

    def __init__(self, context, portlet):
        super(SiteNavtreeStrategy, self).__init__(context, portlet)
        if not portlet.search_base == 'search_base_context':
            self.rootPath = get_root_path(context, portlet)


class Assignment(basenav.Assignment):
    implements(ISiteNavigationPortlet)
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

    @memoize
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

    _template = ViewPageTemplateFile('sitenavigation.pt')
    recurse = ViewPageTemplateFile('sitenavigation_recurse.pt')


class AddForm(base.AddForm):
    form_fields = form.Fields(ISiteNavigationPortlet)
    label = _(u"Add Site Navigation Portlet")
    description = _(u"Shows a site navigation tree.")

    def create(self, data):
        return Assignment(
            name=data.get('name', ""),
            root=data.get('root', ""),
            currentFolderOnly=data.get('currentFolderOnly', False),
            includeTop=data.get('includeTop', False),
            topLevel=data.get('topLevel', 0),
            bottomLevel=data.get('bottomLevel', 0),
            search_base=data.get('search_base', DEFAULT_SEARCH_BASE),
            expand_tree=data.get('expand_tree', False),
            include_dropdown=data.get('include_dropdown', False),
            css_class_main=data.get('css_class_main', ''),
            show_header=data.get('show_header', True)
        )


class EditForm(base.EditForm):
    form_fields = form.Fields(ISiteNavigationPortlet)
    label = _(u"Edit Site Navigation Portlet")
    description = _(u"Shows a site navigation tree.")
