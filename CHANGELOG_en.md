# v0.0.1

- Initial release

# v0.0.2

> Can't remember exactly when

- Improved caching strategy
- Added dependency: `cachetools`

> August 20, 2026 12:33:40

- Added functions: `parse_frames`, `play_parsed_video`, `show_parsed_photo`
- These new functions also enable more interesting use cases, such as **optimizing frame data after parsing** and **multi-process parsing**.
- Videos played with `play_parsed_video` also seem to be smoother than those played with `play_video`? 🤔

> August 21, 2026 12:13:40

- Added a `demo` folder containing a game that uses [`tv.py`](tv.py)

> August 25, 2026 11:29:10

- Added a copyright notice
- Updated the type annotations for `save` and `load`.
- Addressed [issue #1](https://github.com/userwnt/Terminal_Viewer/issues/1) raised by `gurew23`.
- Removed the duplicate `tv.py` under `demo`.

> August 26, 2026 8:53:45

- Fixed the type annotations in [`README`](README_en.md).

> August 26, 2026 12:45:50

- Removed frame caching.
- Increased the pixel-level cache capacity.

> August 27, 2026 13:57:49

- Added an extremely inadequate sleep-time compensation mechanism, with impressively moving results. 😭
- Replaced the demo with a new one.
