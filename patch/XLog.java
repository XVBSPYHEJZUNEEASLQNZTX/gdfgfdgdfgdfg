package org.fptn.vpn.utils;

/**
 * Logging has been removed from this build.
 *
 * This class only keeps the former {@code XLog.tag(TAG).d(...)} call sites compiling. Every
 * method does nothing: no logcat output, no log files, no buffers. The method set mirrors the
 * original library on purpose, so overload resolution in Java and Kotlin stays exactly the same.
 */
public final class XLog {
    private static final Logger NOOP = new Logger();

    private XLog() {
    }

    public static Logger tag(String tag) {
        return NOOP;
    }

    public static final class Logger {
        private Logger() {
        }

        public void v(String format, Object... args) {
        }

        public void v(String msg, Throwable tr) {
        }

        public void v(Object object) {
        }

        public void v(Object[] array) {
        }

        public void d(String format, Object... args) {
        }

        public void d(String msg, Throwable tr) {
        }

        public void d(Object object) {
        }

        public void d(Object[] array) {
        }

        public void i(String format, Object... args) {
        }

        public void i(String msg, Throwable tr) {
        }

        public void i(Object object) {
        }

        public void i(Object[] array) {
        }

        public void w(String format, Object... args) {
        }

        public void w(String msg, Throwable tr) {
        }

        public void w(Object object) {
        }

        public void w(Object[] array) {
        }

        public void e(String format, Object... args) {
        }

        public void e(String msg, Throwable tr) {
        }

        public void e(Object object) {
        }

        public void e(Object[] array) {
        }
    }
}
