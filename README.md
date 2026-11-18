# 502ds.dev

The public pages of 502 Design Studio's apps: one home page, and per app its page, support, privacy policy and terms.

The legal text is not written here: `build.py` reads each app's store documents (`Meridiem/docs/appstore/*.md`), drops
their draft notes and what is held for a later release, fills the bracketed fields from the publishing data kept
outside every repository, and writes static pages to `docs/`.

    python build.py            # for publishing; stops while a field is still empty
    python build.py --draft    # to review, gaps visible, kept out of search engines

`docs/` is built for publishing only, then committed and served as it is.
