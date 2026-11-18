#!/usr/bin/env python3
"""
Turns upstream FptnClient-Android into a build with
  * no Google services (no Firebase, Crashlytics, Analytics, google-services plugin, AD_ID),
  * no logging at all (no logcat, no log files, no log viewer, native logger -> null sink).

Usage:  python3 -I apply_patch.py <path-to-FptnClient-Android-checkout>

Every edit asserts that the text it changes exists exactly once, so if upstream changes and an
edit no longer fits, the script stops with a clear message instead of producing a broken tree.
"""
import pathlib
import re
import sys

if len(sys.argv) != 2:
    sys.exit("usage: apply_patch.py <FptnClient-Android checkout>")

ROOT = pathlib.Path(sys.argv[1]).resolve()
HERE = pathlib.Path(__file__).resolve().parent

JAVA = "app/src/main/java/org/fptn/vpn"
CPP_LIB = "app/src/main/cpp/libs/fptn"


def path(rel):
    p = ROOT / rel
    if not p.exists():
        sys.exit(f"FAIL: {rel} does not exist")
    return p


def read(rel):
    return path(rel).read_text(encoding="utf-8")


def write(rel, text):
    path(rel).write_text(text, encoding="utf-8")


def replace_once(rel, old, new):
    text = read(rel)
    count = text.count(old)
    if count != 1:
        sys.exit(f"FAIL: {rel}: expected exactly 1 match, found {count} for:\n{old[:200]}")
    write(rel, text.replace(old, new, 1))


def remove_once(rel, old):
    replace_once(rel, old, "")


def cut_between(rel, start, end):
    """Remove text from `start` up to (not including) `end`. Both must be unique."""
    text = read(rel)
    for label, marker in (("start", start), ("end", end)):
        if text.count(marker) != 1:
            sys.exit(f"FAIL: {rel}: {label} marker found {text.count(marker)} times:\n{marker[:200]}")
    i, j = text.index(start), text.index(end)
    if i >= j:
        sys.exit(f"FAIL: {rel}: start marker is after end marker")
    write(rel, text[:i] + text[j:])


def delete(rel):
    p = path(rel)
    p.unlink()
    print(f"  deleted  {rel}")


def done(msg):
    print(f"  ok       {msg}")


# ---------------------------------------------------------------------------------------------
print("1/6 Remove the log viewer, log settings and log files")
# ---------------------------------------------------------------------------------------------
for f in (
    f"{JAVA}/ui/logs/LogsScreen.kt",
    f"{JAVA}/ui/logs/LogsViewModel.kt",
    f"{JAVA}/ui/logs/LogsRepository.kt",
    "app/src/test/java/org/fptn/vpn/ui/logs/LogsRepositoryTest.kt",
    f"{JAVA}/utils/XLogInitializer.java",
    f"{JAVA}/enums/AppLogLevel.java",
):
    delete(f)

# App.java: no logger initialisation
app = f"{JAVA}/App.java"
remove_once(app, "import org.fptn.vpn.utils.XLogInitializer;\n")
remove_once(app, "\nimport com.elvishew.xlog.XLog;\n")
remove_once(app, "        initXLog();\n")
remove_once(
    app,
    "\n    private void initXLog() {\n"
    "        XLogInitializer.init(this);\n"
    "        XLog.i(\"XLog initialized successfully [level=%s]\", SharedPrefUtils.getLogLevel(this));\n"
    "    }\n",
)
done("App.java")

# SharedPrefUtils: the saved log level is gone
spu = f"{JAVA}/utils/SharedPrefUtils.java"
remove_once(spu, "import org.fptn.vpn.enums.AppLogLevel;\n")
# "\n}\n" (a brace at column 0) is only the end of the class; the log-level methods are before it.
cut_between(spu, "\n    /* Log level */\n", "\n}\n")
done("SharedPrefUtils.java")

# Settings screen: no 'Logs' row, no log-level picker, no 'Clear logs'
st = f"{JAVA}/ui/settings/SettingsScreen.kt"
remove_once(st, "import org.fptn.vpn.enums.AppLogLevel\n")
remove_once(st, "import org.fptn.vpn.utils.XLogInitializer\n")
remove_once(st, "    onNavigateLogs: () -> Unit,\n")
remove_once(st, "    var showClearLogsConfirm by remember { mutableStateOf(false) }\n")
remove_once(st, "    var logLevel by remember { mutableStateOf(SharedPrefUtils.getLogLevel(context)) }\n")
cut_between(
    st,
    "            SettingsNavRow(\n"
    "                icon = R.drawable.ic_logo_24,\n"
    "                title = stringResource(R.string.logs),\n",
    "            SettingsNavRow(\n"
    "                icon = R.drawable.cloud_back_up_24,\n"
    "                title = stringResource(R.string.backups_title),\n",
)
remove_once(
    st,
    "\n    if (showClearLogsConfirm) {\n"
    "        AlertDialog(\n"
    "            onDismissRequest = { showClearLogsConfirm = false },\n"
    "            title = { Text(stringResource(R.string.dialog_clear_logs_title)) },\n"
    "            text = { Text(stringResource(R.string.dialog_clear_logs_message)) },\n"
    "            confirmButton = {\n"
    "                TextButton(onClick = {\n"
    "                    showClearLogsConfirm = false\n"
    "                    XLogInitializer.clearLogs(context)\n"
    "                    Toast.makeText(context, R.string.logs_cleared, Toast.LENGTH_SHORT).show()\n"
    "                }) { Text(stringResource(R.string.yes)) }\n"
    "            },\n"
    "            dismissButton = {\n"
    "                TextButton(onClick = { showClearLogsConfirm = false }) { Text(stringResource(R.string.no)) }\n"
    "            },\n"
    "        )\n"
    "    }\n",
)
remove_once(
    st,
    "\n@Composable\n"
    "private fun logLevelLabel(level: AppLogLevel): String = when (level) {\n"
    "    AppLogLevel.VERBOSE -> stringResource(R.string.log_level_verbose)\n"
    "    AppLogLevel.DEBUG -> stringResource(R.string.log_level_debug)\n"
    "    AppLogLevel.INFO -> stringResource(R.string.log_level_info)\n"
    "    AppLogLevel.WARN -> stringResource(R.string.log_level_warn)\n"
    "    AppLogLevel.ERROR -> stringResource(R.string.log_level_error)\n"
    "    AppLogLevel.NONE -> stringResource(R.string.log_level_none)\n"
    "}\n",
)
done("SettingsScreen.kt")

# Navigation: no Logs destination
nav = f"{JAVA}/ui/navigation/AppNavHost.kt"
remove_once(nav, "import org.fptn.vpn.ui.logs.LogsScreen\n")
remove_once(nav, '    const val LOGS = "logs"\n')
remove_once(
    nav,
    "        composable(AppRoute.LOGS) {\n"
    "            // Only reachable today from SettingsScreen's nav row.\n"
    "            LogsScreen(\n"
    "                onNavigateHome = {\n"
    "                    navController.navigate(AppRoute.HOME) { launchSingleTop = true }\n"
    "                },\n"
    "                onNavigateSettings = {\n"
    "                    navController.navigate(AppRoute.SETTINGS) { launchSingleTop = true }\n"
    "                },\n"
    "            )\n"
    "        }\n",
)
remove_once(
    nav,
    "                onNavigateLogs = {\n"
    "                    navController.navigate(AppRoute.LOGS) { launchSingleTop = true }\n"
    "                },\n",
)
done("AppNavHost.kt")

# FileProvider: the log directory is no longer shared
remove_once(
    "app/src/main/res/xml/file_paths.xml",
    '    <files-path\n        name="logs"\n        path="logs2/" />\n',
)
done("file_paths.xml")

# ---------------------------------------------------------------------------------------------
print("2/6 Replace the XLog library with a no-op stub (all former call sites stay valid)")
# ---------------------------------------------------------------------------------------------
stub = (HERE / "XLog.java").read_text(encoding="utf-8")
(ROOT / JAVA / "utils" / "XLog.java").write_text(stub, encoding="utf-8")
done("utils/XLog.java added")

import_re = re.compile(r"^import com\.elvishew\.xlog\.XLog(;?)[ \t]*$", re.MULTILINE)
rewritten = 0
for src in (ROOT / "app/src").rglob("*"):
    if src.suffix not in (".java", ".kt") or not src.is_file():
        continue
    text = src.read_text(encoding="utf-8")
    new_text, n = import_re.subn(r"import org.fptn.vpn.utils.XLog\1", text)
    if n:
        src.write_text(new_text, encoding="utf-8")
        rewritten += 1
done(f"{rewritten} files now import the stub")

# ---------------------------------------------------------------------------------------------
print("3/6 Remove Google services and Firebase from the build")
# ---------------------------------------------------------------------------------------------
delete("app/google-services.json")

root_gradle = "build.gradle.kts"
remove_once(
    root_gradle,
    "    dependencies {\n"
    "        classpath(libs.firebase.crashlytics.gradle)\n"
    "        classpath(libs.google.services)\n"
    "    }\n",
)
remove_once(root_gradle, "    alias(libs.plugins.crashlytics) apply false\n")
done("build.gradle.kts")

toml = "gradle/libs.versions.toml"
for line in (
    'crashlytics = "3.0.6"',
    'firebaseBom = "34.11.0"',
    'firebaseCrashlyticsPlugin = "3.0.6"',
    'googlePlayServices = "4.4.4"',
    'firebase-analytics = { group = "com.google.firebase", name = "firebase-analytics" }',
    'firebase-bom = { group = "com.google.firebase", name = "firebase-bom", version.ref = "firebaseBom" }',
    'firebase-crashlytics-gradle = { group = "com.google.firebase", name = "firebase-crashlytics-gradle", version.ref = "firebaseCrashlyticsPlugin" }',
    'firebase-crashlytics-ndk = { group = "com.google.firebase", name = "firebase-crashlytics-ndk" }',
    'google-services = { group = "com.google.gms", name = "google-services", version.ref = "googlePlayServices" }',
    'xlog = { module = "com.elvishew:xlog", version = "1.11.1" }',
    'crashlytics = { id = "com.google.firebase.crashlytics", version.ref = "crashlytics" }',
):
    remove_once(toml, line + "\n")
done("libs.versions.toml")

app_gradle = "app/build.gradle.kts"
remove_once(
    app_gradle,
    "    // Google/Firebase plugins are applied conditionally below — only when a `gms`\n"
    "    // variant is built. This keeps the `foss` APK free of Firebase/Crashlytics and\n"
    "    // means `foss` builds don't require google-services.json.\n"
    '    id("com.google.gms.google-services") apply false\n'
    "    alias(libs.plugins.crashlytics) apply false\n",
)

# The old conditional Google plugin block becomes the build knobs block.
replace_once(
    app_gradle,
    "// Apply the Google/Firebase plugins only when a `gms` variant is being built\n"
    "// (e.g. `bundleGmsRelease` -> AAB for Google Play). `foss` builds\n"
    "// (e.g. `assembleFossRelease` -> APK for sideloading) skip them entirely.\n"
    "val isGmsBuild = gradle.startParameter.taskRequests.any { request ->\n"
    '    request.args.any { it.contains("Gms", ignoreCase = true) }\n'
    "}\n"
    "if (isGmsBuild) {\n"
    '    apply(plugin = "com.google.gms.google-services")\n'
    '    apply(plugin = "com.google.firebase.crashlytics")\n'
    "}\n",
    "// ---- Build knobs (the defaults keep the original behaviour) --------------------------\n"
    "//   -PfptnAbis=arm64-v8a                  build only these ABIs (comma separated)\n"
    "//   -PfptnConanBuildTypes=RelWithDebInfo  run `conan install` only for these build types\n"
    "//   (a release APK is built with RelWithDebInfo, a debug build with Debug)\n"
    'val abiToConanArch = mapOf("arm64-v8a" to "armv8", "armeabi-v7a" to "armv7", "x86_64" to "x86_64")\n'
    "\n"
    "fun csvProperty(name: String, default: List<String>): List<String> =\n"
    "    (findProperty(name) as String?)\n"
    '        ?.split(",")\n'
    "        ?.map { it.trim() }\n"
    "        ?.filter { it.isNotEmpty() }\n"
    "        ?: default\n"
    "\n"
    'val fptnAbis: List<String> = csvProperty("fptnAbis", abiToConanArch.keys.toList())\n'
    "val fptnConanBuildTypes: List<String> =\n"
    '    csvProperty("fptnConanBuildTypes", listOf("Debug", "Release", "RelWithDebInfo"))\n'
    "fptnAbis.forEach { require(it in abiToConanArch) { \"Unsupported ABI in -PfptnAbis: $it\" } }\n",
)

replace_once(
    app_gradle,
    'abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64")',
    "abiFilters += fptnAbis",
)
replace_once(
    app_gradle,
    'include("arm64-v8a", "armeabi-v7a", "x86_64")',
    "include(*fptnAbis.toTypedArray())",
)
cut_between(
    app_gradle,
    '    flavorDimensions += "distribution"\n',
    "    compileOptions {\n",
)
remove_once(
    app_gradle,
    "    // Firebase only in the `gms` flavor (AAB). The `foss` flavor (APK) has none of it.\n"
    '    "gmsImplementation"(platform(libs.firebase.bom))\n'
    '    "gmsImplementation"(libs.firebase.analytics)\n'
    '    "gmsImplementation"(libs.firebase.crashlytics.ndk)\n',
)
replace_once(
    app_gradle,
    "    // Jetpack Compose (single-activity UI). Shared by both `gms` and `foss` flavors.\n",
    "    // Jetpack Compose (single-activity UI).\n",
)
remove_once(app_gradle, "    implementation(libs.xlog)\n")
replace_once(
    app_gradle,
    '        listOf("Debug", "Release", "RelWithDebInfo").forEach { buildType ->\n'
    '            listOf("armv8", "armv7", "x86_64").forEach { arch ->\n',
    "        fptnConanBuildTypes.forEach { buildType ->\n"
    "            fptnAbis.map { abiToConanArch.getValue(it) }.forEach { arch ->\n",
)
done("app/build.gradle.kts (no flavors, no Firebase, ABI/conan knobs)")

manifest = "app/src/main/AndroidManifest.xml"
remove_once(
    manifest,
    "    <uses-permission\n"
    '        android:name="com.google.android.gms.permission.AD_ID"\n'
    '        tools:node="remove" />\n'
    "\n",
)
# Do not let Android Auto Backup copy app data (tokens, settings) to Google Drive.
replace_once(manifest, 'android:allowBackup="true"', 'android:allowBackup="false"')
done("AndroidManifest.xml (AD_ID gone, allowBackup=false)")

# ---------------------------------------------------------------------------------------------
print("4/6 Native code: the logger writes to a null sink and is switched off")
# ---------------------------------------------------------------------------------------------
logger_h = f"{CPP_LIB}/src/common/logger/logger.h"
replace_once(
    logger_h,
    "#include <spdlog/sinks/android_sink.h>  // NOLINT(build/include_order)",
    "#include <spdlog/sinks/null_sink.h>     // NOLINT(build/include_order)",
)
replace_once(
    logger_h,
    '    auto logger = spdlog::android_logger_mt("android", app_name);',
    "    // Logging is disabled in this build: everything goes to a sink that discards it.\n"
    "    auto logger = std::make_shared<spdlog::logger>(\n"
    "        app_name, std::make_shared<spdlog::sinks::null_sink_mt>());",
)
replace_once(
    logger_h,
    "    spdlog::set_level(spdlog::level::info);",
    "#ifdef __ANDROID__\n"
    "    spdlog::set_level(spdlog::level::off);\n"
    "#else\n"
    "    spdlog::set_level(spdlog::level::info);\n"
    "#endif",
)
replace_once(
    logger_h,
    "#ifdef __ANDROID__\n"
    '    __android_log_print(ANDROID_LOG_ERROR, "FPTN",\n'
    '        "Logger initialization failed: %s", ex.what());\n'
    "#else\n",
    "#ifdef __ANDROID__\n"
    "    (void)ex;  // logging is disabled in this build\n"
    "#else\n",
)
done("libs/fptn/src/common/logger/logger.h")

# ---------------------------------------------------------------------------------------------
print("5/6 Native build: conan toolchain loader that tolerates a single build type")
# ---------------------------------------------------------------------------------------------
(ROOT / "app/src/main/cpp/conan_android_toolchain.cmake").write_text(
    (HERE / "conan_android_toolchain.cmake").read_text(encoding="utf-8"), encoding="utf-8"
)
done("conan_android_toolchain.cmake")

# Upstream CI needs a private runner and secrets; it cannot run anywhere else.
wf = ROOT / ".github/workflows/android.yml"
if wf.exists():
    wf.unlink()
    print("  deleted  .github/workflows/android.yml")

# ---------------------------------------------------------------------------------------------
print("6/6 Self-check: nothing of the removed parts may be left in code or build files")
# ---------------------------------------------------------------------------------------------
forbidden = [
    r"com\.elvishew",
    r"XLogInitializer",
    r"AppLogLevel",
    r"LogsScreen|LogsViewModel|LogsRepository",
    r"firebase",
    r"crashlytics",
    r"google-services",
    r"google\.services",
    r"gmsImplementation",
    r"permission\.AD_ID",
    r"android_logger_mt",
    r"__android_log_print",
    r"android_sink",
]
pattern = re.compile("|".join(forbidden), re.IGNORECASE)
scan = []
for base in (ROOT / "app/src/main/java", ROOT / "app/src/test", ROOT / "app/src/androidTest",
             ROOT / "buildSrc/src", ROOT / f"{CPP_LIB}/src/common", ROOT / f"{CPP_LIB}/src/fptn-protocol-lib",
             ROOT / "app/src/main/cpp/src"):
    if base.exists():
        scan += [p for p in base.rglob("*") if p.is_file() and p.suffix in (".java", ".kt", ".kts", ".h", ".cpp", ".cmake", ".txt")]
scan += [ROOT / f for f in ("build.gradle.kts", "settings.gradle.kts", "app/build.gradle.kts",
                            "gradle/libs.versions.toml", "app/src/main/AndroidManifest.xml",
                            "app/src/main/res/xml/file_paths.xml", "app/proguard-rules.pro")]
bad = []
for p in scan:
    for n, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if pattern.search(line):
            bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()[:120]}")
if bad:
    print("\n".join(bad))
    sys.exit("FAIL: leftovers found (see above)")
print("  ok       no leftovers")
print("\nPatch applied.")
