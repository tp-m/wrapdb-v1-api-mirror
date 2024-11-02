# Meson wrapdb v1 api database mirror script

Little script to create a static mirror of the project list, wrap infos,
wraps, and patch zips available in the v1 api database.

The v1 wrapdb API is legacy API used by Meson v0.58 (released on 2 May 2021)
and older versions.

v1 API queries are handled by an application on the wrapdb server which
maintains a local database of the available wraps and wrap versions, and
can also answer search queries.

In contrast, the current v2 wrapdb API is just static files that are served
directly from GitHub, and wrapdb.mesonbuild.com just issues url redirects
to GitHub.

v1 provides two bits of functionality, with a local database maintained on
the wrapdb server:

1. downloads of wraps and patches
2. remote API for listing available wraps and getting info on them

The v1 wrap database is pretty much static at this point, so we can just
mirror the project list, wraps, etc.

The only thing we can't mirror is the substring search query API, but that's
user interactive functionality, so if that stops working that's not too bad
and users will just have to browse the full list or check the website.

The main goal of this script is to maintain wrap/zip download functionality
for older Meson versions by mirroring the database into a static file tree
that can be served directly from the web server, so that the web server
scripts can be retired.

## Usage

```command
./do-mirror-v1.py .
```

will create a `v1-static` directory in the current working directory and mirror
the v1 project list and project infos and all the wraps and zips.

The result has already been checked into the git tree, since it won't change.

## nginx.conf

nginx server config contains

- home page redirect and v2 api redirects to GitHub (not of interest for v1)
- legacy v1 api handling via uswgi has been removed
- decorate static files served from `/v1-static/` with the right
  content-type and where applicable content-disposition headers
  (`v1-static` should be at `/var/www/v1-static`)
- redirects from `/v1/*` api prefix to `/v1-static` (reason: see note below)

**Note:** The static file tree does not 100% match the URI scheme of the v1
API, that's why there are redirects in place. The reason for this is that
in the v1 API the same name is used for files and directories, which works if
the answer is created dynamically but not if it's served from a file system.

Examples:

- `/v1/projects` (list of projects) -> `/v1-static/-/projects`
  - projects is a file
- `/v1/projects/abseil-cpp` (project info) -> `/v1-static/projects/-/abseil-cpp`
  - projects is a directory, abseil-cpp is a file
- `/v1/projects/abseil-cpp/20210324.1/2/get_wrap` (wrap) -> `/v1-static/projects/abseil-cpp/20210324.1/2/-/get_wrap`
  - projects is a directory, abseil-cpp is a directory

## Test URIs

- project list (application/json)
  - https://wrapdb.mesonbuild.com/v1/projects
- latest version (application/json):
  - https://wrapdb.mesonbuild.com/v1/query/get_latest/abseil_cpp
- project info (application/json):
  - https://wrapdb.mesonbuild.com/v1/projects/abseil-cpp
- download wrap (text/plain
  - https://wrapdb.mesonbuild.com/v1/projects/abseil-cpp/20210324.1/2/get_wrap
- download patch/zip (application/zip) (Content-Disposition: attachment; filename=abseil-cpp-20210324.1-2-wrap.zip):
  - https://wrapdb.mesonbuild.com/v1/projects/abseil-cpp/20210324.1/2/get_zip

- Bonus: direct named links to wrap/zip (not used in v1 api, we just added that):
  - https://wrapdb.mesonbuild.com/v1-static/projects/abseil-cpp/20210324.1/2/abseil-cpp-20210324.1-2.wrap
  - https://wrapdb.mesonbuild.com/v1-static/projects/abseil-cpp/20210324.1/2/abseil-cpp-20210324.1-2-wrap.zip
