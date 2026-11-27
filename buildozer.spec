[app]
title = 仓位止损计算器
package.name = stoploss
package.domain = org.local
source.dir = .
source.include_exts = py
source.exclude_dirs = archive,bin,.github,.buildozer
version = 1.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
