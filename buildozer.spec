[app]

title = Student Details
package.name = studentdetailsapp
package.domain = org.test
source.dir = .
source.include_exts = py,kv,png,jpg,txt,db,xlsx
version = 1.0
requirements = python3,kivy,kivymd,pandas,openpyxl,sqlite3
orientation = portrait
osx.python_version = 3
fullscreen = 1

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = armeabi-v7a, arm64-v8a

android.allow_backup = 1
android.private_storage = True

android.gradle_dependencies = com.android.support:appcompat-v7:28.0.0

# To avoid unnecessary modules
exclude_dirs = tests,bin,build,__pycache__,.git

[buildozer]
log_level = 2
warn_on_root = 1
