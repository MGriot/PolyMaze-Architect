[app]
# Android build. Buildozer runs on Linux only: use WSL2 (Ubuntu) or the CI workflow.
#     buildozer android debug             -> bin/*-debug.apk (sideload / emulator, throwaway debug key)
#     buildozer android release           -> bin/*-release.apk (signed with the P4A_RELEASE_* key, see docs/packaging.md)
title = PolyMaze Architect
package.name = polymazearchitect
# Permanent app id: io.github.mgriot.polymazearchitect. Changing it makes a different app that can't upgrade this one.
package.domain = io.github.mgriot

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
# GitHub Releases ship a sideloadable APK. For Google Play switch the release artifact to aab.
android.release_artifact = apk
android.debug_artifact = apk
# Lets unattended builds (CI) download the SDK; you are accepting the Android SDK license.
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
