"""Resilient Selenium driver initialisation helpers for LinkedIn automation.

Why:
    LinkedIn frequently tightens bot detection; abstracting driver setup allows
    us to tweak launch strategies centrally.

When:
    Imported during bot instantiation to obtain a configured Chrome/Chromium
    WebDriver capable of bypassing common detection heuristics.

How:
    Detects platform specifics, attempts multiple driver strategies (local
    binaries, undetected-chromedriver, webdriver-manager), and returns a ready
    driver instance.
"""

import os
import platform
import logging
import shutil
import subprocess
import time

from . import config

# Heavy Selenium / undetected_chromedriver / webdriver_manager imports are
# **deferred** to ``setup_driver()`` so importing this module (e.g. for type
# hints or unrelated CLI paths like ``generate-calendar``) is essentially
# free. They're cached in ``sys.modules`` after first use, so repeat calls
# pay no penalty.


class DriverFactory:
    """Factory utilities for provisioning Chrome-based Selenium drivers.

    Why:
        Encapsulate OS detection, binary discovery, and fallback strategies so
        the rest of the codebase simply calls :meth:`setup_driver`.

    When:
        Invoked whenever a new automation session begins.

    How:
        Offers static helpers that search for browser binaries, configure
        options, and cascade through multiple launch strategies until a driver
        succeeds or all attempts fail.
    """

    _uc_teardown_patch_applied = False

    @staticmethod
    def _apply_uc_teardown_patch() -> None:
        """Prevent ``Chrome.__del__`` from re-running ``quit()`` after explicit teardown.

        undetected-chromedriver's destructor always calls ``quit()``; on Windows
        a second ``quit()`` during interpreter shutdown often raises
        ``OSError: [WinError 6] The handle is invalid`` (harmless but noisy).
        """
        if DriverFactory._uc_teardown_patch_applied:
            return
        try:
            import undetected_chromedriver as uc
        except ImportError:
            return

        _orig_quit = uc.Chrome.quit
        _orig_del = uc.Chrome.__del__

        def quit_patched(self):
            try:
                return _orig_quit(self)
            finally:
                try:
                    self.__dict__["__linkedin_automation_uc_quit"] = True
                except Exception:
                    pass

        def del_patched(self):
            if getattr(self, "__linkedin_automation_uc_quit", False):
                return
            try:
                return _orig_del(self)
            except OSError:
                pass

        uc.Chrome.quit = quit_patched  # type: ignore[method-assign]
        uc.Chrome.__del__ = del_patched  # type: ignore[method-assign]
        DriverFactory._uc_teardown_patch_applied = True

    @staticmethod
    def _wait_for_browser_window(driver, timeout_seconds: float | None = None) -> bool:
        """Block until at least one top-level window is attached (UC + Windows race).

        undetected-chromedriver often returns from ``Chrome()`` before the first
        window is addressable; ``get()`` then raises ``NoSuchWindowException``.
        """
        if timeout_seconds is None:
            timeout_seconds = 35.0 if platform.system() == "Windows" else 20.0
        deadline = time.monotonic() + float(timeout_seconds)
        last_err: Exception | None = None
        interval = 0.2
        logged_wait = False
        started = time.monotonic()
        while time.monotonic() < deadline:
            try:
                handles = driver.window_handles
                if handles:
                    driver.switch_to.window(handles[0])
                driver.current_window_handle
                return True
            except Exception as e:
                last_err = e
                if not logged_wait and time.monotonic() - started > 2.0:
                    logging.info(
                        "Waiting for Chrome window to attach (%.0fs max, common on Windows with UC)...",
                        timeout_seconds,
                    )
                    logged_wait = True
                time.sleep(interval)
                interval = min(interval * 1.12, 0.9)
        logging.error(
            "Chrome did not expose a usable window within %.0fs: %s",
            timeout_seconds,
            last_err,
        )
        return False

    @staticmethod
    def setup_driver():
        """Provision a Selenium WebDriver resilient to LinkedIn bot detection.

        Why:
            LinkedIn frequently changes detection heuristics; wrapping setup in
            a single method allows us to tune the launch sequence quickly.

        When:
            Called during :class:`LinkedInBot` construction before any LinkedIn
            page is accessed.

        How:
            Detects the host OS, resolves browser paths/versions, configures
            undetected-chromedriver options, and sequentially tries local
            chromedriver, undetected-chromedriver, and webdriver-manager
            fallbacks, returning the first successful driver.

        Returns:
            webdriver.Chrome: A configured Chrome or Chromium Selenium driver.

        Raises:
            Exception: Propagates when every initialisation strategy fails.
        """
        try:
            # Detect OS platform
            system = platform.system()
            logging.info(f"Detected operating system: {system}")
            
            # Different browser paths and commands based on OS
            browser_paths, version_commands = DriverFactory._get_platform_specific_paths(system)
            
            # Try to detect browser version
            browser_version = DriverFactory._detect_browser_version(version_commands)
            
            # Find the first existing browser path
            browser_path = DriverFactory._find_browser_path(browser_paths)
            
            # Configure undetected-chromedriver options
            options = DriverFactory._configure_browser_options()
            
            # Try multiple initialization strategies
            driver = DriverFactory._initialize_driver_with_fallbacks(browser_path, browser_version, options)

            # UC often returns before the first window is navigable (especially on Windows).
            time.sleep(1.0 if platform.system() == "Windows" else 0.65)
            if not DriverFactory._wait_for_browser_window(driver):
                logging.warning(
                    "Chrome window wait timed out; login will still retry navigation. "
                    "Quit other Chrome instances, disable 'Continue running background apps', "
                    "and avoid starting two bots at once."
                )

            logging.info("Successfully initialized ChromeDriver")
            return driver
        except Exception as e:
            logging.error(f"All ChromeDriver initialization attempts failed: {str(e)}")
            raise
            
    @staticmethod
    def _get_platform_specific_paths(system):
        """Derive candidate browser binaries and version commands per OS.

        Why:
            Chrome/Chromium installs vary by platform; providing tailored search
            paths improves the odds of finding the browser.

        When:
            Executed early in :meth:`setup_driver` prior to driver initialisation.

        How:
            Returns platform-specific tuples containing likely executable paths
            and corresponding ``--version`` commands.

        Args:
            system (str): OS name from :func:`platform.system`.

        Returns:
            tuple[list[str], list[tuple[str, str]]]: Candidate paths and version
            command pairs.
        """
        if system == "Linux":
            browser_paths = ["/usr/bin/chromium", "/usr/bin/chrome", "/usr/bin/google-chrome"]
            version_commands = [("chromium", "--version"), ("google-chrome", "--version")]
        elif system == "Darwin":  # macOS
            browser_paths = [
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ]
            version_commands = [("Chromium", "--version"), ("Google Chrome", "--version")]
        elif system == "Windows":
            browser_paths = [
                os.path.expandvars("%ProgramFiles%\\Chromium\\Application\\chrome.exe"),
                os.path.expandvars("%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"),
                os.path.expandvars("%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe")
            ]
            version_commands = [("chromium", "--version"), ("chrome", "--version")]
        else:
            logging.warning(f"Unknown operating system: {system}")
            browser_paths = []
            version_commands = []
        
        return browser_paths, version_commands
            
    @staticmethod
    def _detect_browser_version(version_commands):
        """Probe available browsers to retrieve a version string.

        Why:
            Some driver strategies need the installed browser version to select
            matching binaries.

        When:
            Called from :meth:`setup_driver` after collecting platform-specific
            commands.

        How:
            Iterates over command tuples, runs them via ``subprocess``, and
            returns the first successful output.

        Args:
            version_commands (list[tuple[str, str]]): Command/argument pairs to
                execute.

        Returns:
            str | None: Detected version string or ``None`` when detection fails.
        """
        browser_version = None
        for cmd, arg in version_commands:
            try:
                version_output = subprocess.check_output([cmd, arg], text=True, stderr=subprocess.STDOUT)
                browser_version = version_output.strip()
                logging.info(f"Browser version: {browser_version}")
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        # Windows-specific fallback to detect version from directory name
        if not browser_version and platform.system() == "Windows":
            logging.info("Attempting to detect Chrome version from Windows file system")
            candidate_dirs = [
                os.path.expandvars("%ProgramFiles%\\Google\\Chrome\\Application"),
                os.path.expandvars("%ProgramFiles(x86)%\\Google\\Chrome\\Application")
            ]
            for app_dir in candidate_dirs:
                if os.path.exists(app_dir):
                    # Look for directories that look like version numbers (e.g., 146.0.7680.165)
                    try:
                        versions = [d for d in os.listdir(app_dir) if os.path.isdir(os.path.join(app_dir, d)) and d and d[0].isdigit() and "." in d]
                        if versions:
                            # Use the most recent/highest version found
                            browser_version = sorted(versions, key=lambda x: [int(v) for v in x.split('.') if v.isdigit()], reverse=True)[0]
                            logging.info(f"Detected browser version from filesystem: {browser_version}")
                            break
                    except Exception as e_dir:
                        logging.warning(f"Error listing version directories in {app_dir}: {e_dir}")
        
        if not browser_version:
            logging.warning("Could not determine browser version")
            
        return browser_version
    
    @staticmethod
    def _find_browser_path(browser_paths):
        """Locate the first existing browser executable from candidate paths.

        Why:
            Passing an explicit binary to Selenium improves reliability when
            multiple versions coexist.

        When:
            Executed during driver setup after gathering OS-specific locations.

        How:
            Iterates over supplied paths and returns the first that exists on the
            filesystem.

        Args:
            browser_paths (list[str]): Candidate absolute paths.

        Returns:
            str | None: Resolved path or ``None`` if none are present.
        """
        browser_path = None
        for path in browser_paths:
            if os.path.exists(path):
                browser_path = path
                logging.info(f"Found browser at: {browser_path}")
                break
        return browser_path
    
    @staticmethod
    def _chrome_profile_dir() -> str | None:
        path = (os.getenv("LINKDAPPLY_CHROME_PROFILE_DIR") or "").strip()
        return path or None

    @staticmethod
    def _apply_chrome_profile_options(options) -> bool:
        """Reuse the job bot's saved Chrome profile when ``LINKDAPPLY_CHROME_PROFILE_DIR`` is set."""
        profile_dir = DriverFactory._chrome_profile_dir()
        if not profile_dir:
            return False
        from services.chrome_profiles import clear_chrome_profile_locks

        os.makedirs(profile_dir, exist_ok=True)
        clear_chrome_profile_locks(profile_dir)
        options.add_argument(f"--user-data-dir={profile_dir}")
        port = (os.getenv("CHROME_DEBUG_PORT") or "").strip()
        if port.isdigit():
            options.add_argument(f"--remote-debugging-port={port}")
        logging.info("Using job-bot Chrome profile: %s", profile_dir)
        return True

    @staticmethod
    def _configure_browser_options():
        """Build Chrome options tuned for automation while mimicking humans.

        Why:
            Applying consistent arguments (headless toggles, window sizing,
            custom UA) reduces flakiness and detection likelihood.

        When:
            Called before any driver initialisation strategy is attempted.

        How:
            Creates :class:`uc.ChromeOptions`, applies sandbox, headless, window,
            and notification arguments based on config.

        Returns:
            uc.ChromeOptions: Options object ready for driver creation.
        """
        import undetected_chromedriver as uc  # deferred: heavy import

        options = uc.ChromeOptions()
        
        # Basic configuration
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Apply headless mode if configured
        if config.HEADLESS:
            options.add_argument("--headless")
            
        # Set window size
        options.add_argument(f"--window-size={config.WINDOW_SIZE[0]},{config.WINDOW_SIZE[1]}")
        
        # Disable notifications and add custom user agent
        options.add_argument("--disable-notifications")
        options.add_argument(f"user-agent={config.USER_AGENT}")

        DriverFactory._apply_chrome_profile_options(options)

        return options
    
    @staticmethod
    def _initialize_driver_with_fallbacks(browser_path, browser_version, options):
        """Attempt multiple driver launch strategies until one succeeds.

        Why:
            Different environments require different launch paths; chaining
            fallbacks maximises success without manual intervention.

        When:
            Called from :meth:`setup_driver` after collecting platform details
            and options.

        How:
            Tries local chromedriver, undetected-chromedriver (two variants),
            and webdriver-manager, returning as soon as a driver initialises.

        Args:
            browser_path (str | None): Preferred browser binary path.
            browser_version (str | None): Detected browser version string.
            options (uc.ChromeOptions): Preconfigured options for launch.

        Returns:
            webdriver.Chrome: Successfully initialised driver instance.

        Raises:
            Exception: Propagated when all strategies fail.
        """
        # Deferred imports: only paid when we actually need to launch a
        # browser, which excludes ``--help`` and ``generate-calendar``.
        import undetected_chromedriver as uc
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager, ChromeType

        DriverFactory._apply_uc_teardown_patch()

        # 0) Prefer a locally installed chromedriver to avoid network
        local_driver_path = DriverFactory._find_local_chromedriver()
        if local_driver_path:
            try:
                logging.info(f"Attempting local ChromeDriver at: {local_driver_path}")
                # Build standard ChromeOptions mirroring our settings
                std_options = webdriver.ChromeOptions()
                std_options.add_argument("--no-sandbox")
                std_options.add_argument("--disable-dev-shm-usage")
                if config.HEADLESS:
                    std_options.add_argument("--headless=new")
                std_options.add_argument(f"--window-size={config.WINDOW_SIZE[0]},{config.WINDOW_SIZE[1]}")
                std_options.add_argument("--disable-notifications")
                std_options.add_argument(f"user-agent={config.USER_AGENT}")
                DriverFactory._apply_chrome_profile_options(std_options)
                # If we detected a browser binary, point to it
                if browser_path:
                    try:
                        std_options.binary_location = browser_path
                    except Exception:
                        pass
                service = Service(local_driver_path)
                driver = webdriver.Chrome(service=service, options=std_options)
                return driver
            except Exception as e_local:
                logging.warning(f"Local ChromeDriver init failed: {e_local}")

        # 1) Try undetected-chromedriver (may require network for patching)
        try:
            logging.info("Attempting to use undetected-chromedriver (system/auto)")
            driver_args = {
                "options": options,
                "use_subprocess": True,
                "driver_executable_path": False
            }
            if browser_path:
                driver_args["browser_executable_path"] = browser_path
            
            # Pass major version if detected to avoid mismatch (especially on Windows)
            if browser_version:
                try:
                    # Extract major version number (e.g. from "146.0.7680.165" or "Chrome 146...")
                    import re
                    match = re.search(r'(\d+)\.', browser_version)
                    if match:
                        major = int(match.group(1))
                        driver_args["version_main"] = major
                        logging.info(f"Informing undetected-chromedriver of version_main={major}")
                except Exception as e_v:
                    logging.warning(f"Could not parse major version from '{browser_version}': {e_v}")

            driver = uc.Chrome(**driver_args)
            return driver
        except Exception as e1:
            logging.warning(f"undetected-chromedriver init failed: {str(e1)}. Retrying with default.")

            # 2) Retry default undetected-chromedriver init
            try:
                logging.info("Attempting default undetected-chromedriver initialization")
                # Re-create options to avoid "cannot reuse" error
                new_options = DriverFactory._configure_browser_options()
                driver_args = {
                    "options": new_options,
                    "use_subprocess": True
                }
                if browser_path:
                    driver_args["browser_executable_path"] = browser_path
                    
                # Reuse version_main if we have it
                if "version_main" in locals() or ("driver_args" in locals() and "version_main" in driver_args):
                    major = driver_args.get("version_main")
                    if major:
                         driver_args["version_main"] = major

                driver = uc.Chrome(**driver_args)
                return driver
            except Exception as e2:
                logging.warning(f"Second undetected-chromedriver init failed: {str(e2)}. Trying Selenium Manager (may need network).")

                # 3) Selenium Manager via webdriver-manager (requires network)
                logging.info("Attempting fallback to standard selenium ChromeDriver via webdriver-manager")
                chrome_type = ChromeType.CHROMIUM if browser_version and "chromium" in str(browser_version).lower() else ChromeType.GOOGLE
                logging.info(f"Using ChromeType: {chrome_type}")
                service = Service(ChromeDriverManager(chrome_type=chrome_type).install())
                driver = webdriver.Chrome(service=service, options=options)
                return driver

    @staticmethod
    def _find_local_chromedriver():
        """Search common locations for an existing chromedriver binary.

        Why:
            Using a local binary avoids network downloads and speeds up start-up.

        When:
            Invoked prior to falling back to undetected-chromedriver or
            webdriver-manager.

        How:
            Checks environment variables, PATH, and common installation paths
            and returns the first binary discovered.

        Returns:
            str | None: Path to chromedriver or ``None`` when not found.
        """
        # 1) Explicit env var
        for env_name in ("CHROMEDRIVER_PATH", "CHROMEWEBDRIVER", "WEBDRIVER_CHROME_DRIVER"):
            path = os.getenv(env_name)
            if path and os.path.exists(path):
                return path
        # 2) In PATH
        path = shutil.which("chromedriver")
        if path:
            return path
        # 3) Common locations
        common_paths = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
            "/snap/bin/chromedriver",
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p
        return None
