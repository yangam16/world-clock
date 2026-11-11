# Third-party dependencies

The source archive contains the project's Python, shell and documentation files.
GTK, PyGObject, Pycairo, Pango, Ayatana AppIndicator and time-zone data are supplied
by Ubuntu packages and retain their respective upstream licenses.

- GTK: https://www.gtk.org/
- PyGObject: https://pygobject.gnome.org/
- Pycairo: https://pycairo.readthedocs.io/
- Pango: https://docs.gtk.org/Pango/
- Ayatana AppIndicator: https://github.com/AyatanaIndicators/libayatana-appindicator
- IANA time-zone database: https://www.iana.org/time-zones

An optional `vendor/` directory may exist in a developer's local checkout. It is
excluded from Git and the allowlisted source archive. The public installation
uses system packages and does not redistribute the local Ubuntu `.deb` or its
architecture-specific typelib. If redistributing dependencies in another package,
review and include the relevant upstream license notices separately.

When run from a developer checkout that already contains the local typelib,
the per-user installer copies that fallback together with its Ubuntu copyright
notice. A public source checkout uses the system-installed typelib instead.

The project's own source is distributed under the MIT license in `LICENSE`.
