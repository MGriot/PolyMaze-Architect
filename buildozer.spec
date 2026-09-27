[app]
# Android build. Buildozer runs on Linux only: use WSL2 (Ubuntu) or the CI workflow.
#     buildozer android debug             -> bin/*.apk (sideload / emulator)
#     buildozer android release           -> bin/*.aab (Play Store, needs a signing key)
title = PolyMaze Architect
package.name = polymazearchitect
# Change to a domain you own before publishing; it becomes the permanent app id.
package.domain = io.github.polymaze

source.dir = src
source.include_exts = py,png,json
source.exclude_dirs = __pycache__

version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/polymaze/__init__.py

requirements = python3,kivy==2.3.1

icon.filename = %(source.dir)s/polymaze/assets/icon.png
presplash.filename = %(source.dir)s/polymaze/assets/presplash.png
android.presplash_color = #141414

orientation = landscape
fullscreen = 1

# Saves use App.user_data_dir (app-private storage), so no permissions are needed.
android.permissions =
# Google Play requires a recent target API; bump this to the level Play currently demands.
android.api = 35
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.release_artifact = aab
android.debug_artifact = apk
# Lets unattended builds (CI) download the SDK; you are accepting the Android SDK license.
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
