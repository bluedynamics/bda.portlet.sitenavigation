Changelog
=========

2.1 (2015-12-14)
----------------

- Make cache time configurable and set it to 0 seconds. 0 is no caching. There were some issues, where content changes did not reflect in the menus. A good value might be 10 seconds to avoid unnecessary recalculating.
  [thet]


2.0 (2015-07-15)
----------------

- Move all memoize-instance cached methods from plone.app.portlet's navigation
  portlet to this implementation to apply ram caching on it. Avoids some more
  write-on-reads.
  [thet]

- Get rid of write-on-reads and their conflicts by reducing the number of 
  instance memoizes.
  [jensens]

- Cache the rendered portlet for an hour with sensible cache keys (portlet_id,
  path, user) for maximum 1 hour.
  [thet]

- Make ``search_base`` required, so that at least the first item of the
  vocabulary is preselected.
  [thet]

- Change ``css_class_main`` from a TextLine field to a Choice Field, making it
  possible to choose from a vocabulary with nice sounding titles instead of
  having to fill in CSS classes directly. Overrideable via ``overrides.zcml``.
  [thet]

- Switch to ``z3c.form`` for the ``AddForm`` and ``EditForm``.
  [thet]

- Remove the browserlayer, which is nowhere used.
  [thet]


1.0 (2015-03-04)
----------------

- Initial version.
  [thet]
