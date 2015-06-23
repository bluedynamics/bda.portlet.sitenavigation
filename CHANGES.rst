Changelog
=========

2.0 (unreleased)
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
