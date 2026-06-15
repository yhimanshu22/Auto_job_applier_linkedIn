use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::{Manager, State, WebviewUrl, WebviewWindow, WebviewWindowBuilder};
use tauri_plugin_deep_link::DeepLinkExt;
use tauri_plugin_opener::OpenerExt;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

mod production;
mod runtime_config;

use runtime_config::RuntimeConfig;

/// Set once at startup; used for dashboard URL, auth callbacks, and sidecar env.
static RUNTIME_CONFIG: Mutex<Option<RuntimeConfig>> = Mutex::new(None);

fn runtime_config() -> RuntimeConfig {
    RUNTIME_CONFIG
        .lock()
        .ok()
        .and_then(|g| g.clone())
        .expect("runtime config not initialized")
}

struct BackendProcess(Mutex<Option<CommandChild>>);

fn user_data_dir() -> PathBuf {
    if let Ok(dir) = std::env::var("LINKDAPPLY_USER_DATA") {
        let path = PathBuf::from(dir);
        let _ = std::fs::create_dir_all(&path);
        return path;
    }
    let path = dirs::data_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("LinkdApply");
    let _ = std::fs::create_dir_all(&path);
    path
}

#[cfg(debug_assertions)]
fn backend_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../backend")
}

fn api_port() -> u16 {
    std::env::var("LINKDAPPLY_API_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8000)
}

fn local_api_url(port: u16) -> String {
    format!("http://127.0.0.1:{port}")
}

fn dashboard_url() -> String {
    let mut url = runtime_config().dashboard_login_url;

    // Legacy installs that still point at /dashboard get sent to login first.
    if url.contains("/dashboard") && !url.contains("/login") {
        let origin = frontend_origin_from_dashboard_url(&url)
            .unwrap_or_else(|| production::FRONTEND_URL.to_string());
        url = format!(
            "{origin}/login?desktop=1&callbackUrl=%2Fdashboard%3Fdesktop%3D1"
        );
    }

    if !url.contains("desktop=1") {
        let sep = if url.contains('?') { '&' } else { '?' };
        url.push_str(&format!("{sep}desktop=1"));
    }

    url
}

/// Origin (scheme + host) from a dashboard URL, e.g. `https://app.example.com`.
fn frontend_origin_from_dashboard_url(dashboard: &str) -> Option<String> {
    let base = dashboard.split('?').next()?.trim_end_matches('/');
    let scheme_sep = base.find("://")?;
    let scheme = &base[..scheme_sep];
    let after_scheme = &base[scheme_sep + 3..];
    let host_end = after_scheme.find('/').unwrap_or(after_scheme.len());
    let host = &after_scheme[..host_end];
    if host.is_empty() {
        return None;
    }
    Some(format!("{scheme}://{host}"))
}

fn pct_encode_component(s: &str) -> String {
    s.bytes()
        .map(|b| match b {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                (b as char).to_string()
            }
            _ => format!("%{b:02X}"),
        })
        .collect()
}

/// Google OAuth and NextAuth sign-in must run in the system browser, not the WebView.
fn should_open_auth_externally(url: &str) -> bool {
    let lower = url.to_ascii_lowercase();
    lower.contains("accounts.google.com")
        || lower.contains("oauth2.googleapis.com")
        || lower.contains("/api/auth/signin")
}

fn token_from_deep_link(url: &str) -> Option<String> {
    let trimmed = url.trim();
    if !trimmed.to_ascii_lowercase().starts_with("linkdapply://") {
        return None;
    }
    let query = trimmed.split('?').nth(1)?;
    for pair in query.split('&') {
        let (key, value) = pair.split_once('=')?;
        if key == "token" && !value.is_empty() {
            return Some(value.to_string());
        }
    }
    None
}

fn complete_auth_url(origin: &str, token: &str) -> String {
    format!(
        "{}/api/auth/desktop/complete?token={}",
        origin.trim_end_matches('/'),
        pct_encode_component(token)
    )
}

fn navigate_main_to_auth_complete(window: &WebviewWindow, token: &str) {
    let origin = frontend_origin_from_dashboard_url(&dashboard_url())
        .unwrap_or_else(|| production::FRONTEND_URL.to_string());
    let target = complete_auth_url(&origin, token);
    if let Ok(parsed) = target.parse() {
        let _ = window.navigate(parsed);
    }
}

fn handle_deep_link_urls(window: &WebviewWindow, urls: &[tauri::Url]) {
    for url in urls {
        if let Some(token) = token_from_deep_link(url.as_str()) {
            navigate_main_to_auth_complete(window, &token);
            return;
        }
    }
}

fn wait_for_health(port: u16, timeout: Duration) -> bool {
    let url = format!("http://127.0.0.1:{port}/api/health");
    let client = match reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()
    {
        Ok(c) => c,
        Err(_) => return false,
    };
    let start = Instant::now();
    while start.elapsed() < timeout {
        if let Ok(res) = client.get(&url).send() {
            if res.status().is_success() {
                return true;
            }
        }
        std::thread::sleep(Duration::from_millis(400));
    }
    false
}

fn sidecar_env(
    cmd: tauri_plugin_shell::process::Command,
    user_data: &PathBuf,
    host: &str,
    port_str: &str,
    config: &RuntimeConfig,
) -> tauri_plugin_shell::process::Command {
    // Drop inherited VIRTUAL_ENV (wrong project venv breaks `uv run`).
    let envs: Vec<(String, String)> = std::env::vars()
        .filter(|(key, _)| key != "VIRTUAL_ENV")
        .collect();

    let mut cmd = cmd
        .env_clear()
        .envs(envs)
        .env("LINKDAPPLY_USER_DATA", user_data.as_os_str())
        .env("LINKDAPPLY_LOCAL_DATA", "true")
        .env("LINKDAPPLY_API_HOST", host)
        .env("LINKDAPPLY_API_PORT", port_str)
        .env("FRONTEND_URL", config.frontend_url.as_str())
        .env("EXTRA_CORS_ORIGINS", config.extra_cors_origins.as_str())
        .env("NEXTAUTH_SESSION_URL", config.session_url.as_str())
        .env("CLOUD_API_URL", config.cloud_api_url.as_str());

    if let Some(key) = config.internal_key.as_deref() {
        cmd = cmd.env("LINKDAPPLY_INTERNAL_KEY", key);
    }

    cmd
}

fn spawn_child(cmd: tauri_plugin_shell::process::Command) -> Result<CommandChild, String> {
    cmd.spawn()
        .map(|(_events, child)| child)
        .map_err(|e| e.to_string())
}

fn spawn_backend(
    app: &tauri::AppHandle,
    user_data: &PathBuf,
    port: u16,
    config: &RuntimeConfig,
) -> Result<CommandChild, String> {
    let shell = app.shell();
    let host = "127.0.0.1";
    let port_str = port.to_string();

    #[cfg(debug_assertions)]
    {
        let backend = backend_root();
        if backend.join("server.py").exists() {
            let uv = sidecar_env(
                shell
                    .command("uv")
                    .args([
                        "run",
                        "python",
                        "-m",
                        "uvicorn",
                        "server:app",
                        "--host",
                        host,
                        "--port",
                        &port_str,
                    ])
                    .current_dir(&backend),
                user_data,
                host,
                &port_str,
                config,
            );

            if let Ok(child) = spawn_child(uv) {
                return Ok(child);
            }

            return spawn_child(sidecar_env(
                shell
                    .command("python")
                    .args([
                        "-m",
                        "uvicorn",
                        "server:app",
                        "--host",
                        host,
                        "--port",
                        &port_str,
                    ])
                    .current_dir(&backend),
                user_data,
                host,
                &port_str,
                config,
            ));
        }
    }

    spawn_child(sidecar_env(
        shell.sidecar("linkdapply-backend").map_err(|e| e.to_string())?,
        user_data,
        host,
        &port_str,
        config,
    ))
}

fn stop_backend(state: &State<'_, BackendProcess>) {
    if let Ok(mut guard) = state.0.lock() {
        if let Some(child) = guard.take() {
            let _ = child.kill();
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let port = api_port();
    let user_data = user_data_dir();
    runtime_config::write_env_template_if_missing(&user_data);
    let config = runtime_config::load(&user_data);
    if let Ok(mut guard) = RUNTIME_CONFIG.lock() {
        *guard = Some(config.clone());
    }

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_deep_link::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(move |app| {
            let handle = app.handle().clone();
            let child = spawn_backend(&handle, &user_data, port, &config).map_err(|e| {
                std::io::Error::new(
                    std::io::ErrorKind::Other,
                    format!("Failed to start local backend: {e}"),
                )
            })?;

            if let Some(state) = app.try_state::<BackendProcess>() {
                if let Ok(mut guard) = state.0.lock() {
                    *guard = Some(child);
                }
            }

            if !wait_for_health(port, Duration::from_secs(90)) {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::TimedOut,
                    "Local backend did not become healthy on /api/health",
                )
                .into());
            }

            let url = dashboard_url();
            let local_api = local_api_url(port);
            let inject = format!(
                "window.__LINKDAPPLY_DESKTOP__ = {{ localApi: '{local_api}' }}; \
                 try {{ localStorage.setItem('linkdapply_desktop', '1'); }} catch (e) {{}}"
            );

            let app_handle = app.handle().clone();
            let window = WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url.parse().unwrap()))
                .title("LinkdApply")
                .inner_size(1280.0, 860.0)
                .initialization_script(&inject)
                .on_navigation(move |nav_url| {
                    let href = nav_url.as_str();
                    if should_open_auth_externally(href) {
                        let _ = app_handle.opener().open_url(href, None::<&str>);
                        return false;
                    }
                    true
                })
                .build()?;

            #[cfg(any(target_os = "linux", target_os = "windows"))]
            {
                let _ = app.deep_link().register_all();
            }

            let main_window = window.clone();
            app.deep_link().on_open_url(move |event| {
                handle_deep_link_urls(&main_window, &event.urls());
            });

            if let Ok(Some(start_urls)) = app.deep_link().get_current() {
                handle_deep_link_urls(&window, &start_urls);
            }

            let _ = window;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if let Some(state) = window.app_handle().try_state::<BackendProcess>() {
                    stop_backend(&state);
                }
            }
        })
        .run(tauri::generate_context!())
        .unwrap_or_else(|e| {
            #[cfg(windows)]
            show_startup_error(&e.to_string());
            #[cfg(not(windows))]
            eprintln!("LinkdApply failed to start: {e}");
            std::process::exit(1);
        });
}

#[cfg(windows)]
fn show_startup_error(message: &str) {
    use std::ffi::OsStr;
    use std::os::windows::ffi::OsStrExt;

    fn wide(s: &str) -> Vec<u16> {
        OsStr::new(s).encode_wide().chain(Some(0)).collect()
    }

    let text = format!("LinkdApply could not start:\n\n{message}");
    unsafe {
        windows_sys::Win32::UI::WindowsAndMessaging::MessageBoxW(
            std::ptr::null_mut(),
            wide(&text).as_ptr(),
            wide("LinkdApply").as_ptr(),
            windows_sys::Win32::UI::WindowsAndMessaging::MB_ICONERROR
                | windows_sys::Win32::UI::WindowsAndMessaging::MB_OK,
        );
    }
}
