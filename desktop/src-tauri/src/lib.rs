use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::{Manager, State, WebviewUrl, WebviewWindowBuilder};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

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
    let mut url = std::env::var("LINKDAPPLY_FRONTEND_URL")
        .unwrap_or_else(|_| "https://frontend-pink-phi-37.vercel.app/dashboard?desktop=1".to_string());

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
        .env("LINKDAPPLY_API_PORT", port_str);

    if let Ok(cloud) = std::env::var("CLOUD_API_URL") {
        if !cloud.trim().is_empty() {
            cmd = cmd.env("CLOUD_API_URL", cloud.trim());
        }
    }
    if let Ok(key) = std::env::var("LINKDAPPLY_INTERNAL_KEY") {
        if !key.trim().is_empty() {
            cmd = cmd.env("LINKDAPPLY_INTERNAL_KEY", key.trim());
        }
    }

    // When the webview loads a hosted dashboard, the sidecar must verify sessions
    // and allow CORS against that origin (unless already set in desktop/.env).
    if std::env::var("FRONTEND_URL").is_err() {
        if let Ok(dashboard) = std::env::var("LINKDAPPLY_FRONTEND_URL") {
            if let Some(origin) = frontend_origin_from_dashboard_url(&dashboard) {
                cmd = cmd.env("FRONTEND_URL", origin.trim());
                if std::env::var("EXTRA_CORS_ORIGINS").is_err() {
                    cmd = cmd.env("EXTRA_CORS_ORIGINS", origin.trim());
                }
                if std::env::var("NEXTAUTH_SESSION_URL").is_err() {
                    let session = format!("{}/api/auth/session", origin.trim().trim_end_matches('/'));
                    cmd = cmd.env("NEXTAUTH_SESSION_URL", session);
                }
            }
        }
    }

    cmd
}

fn spawn_child(cmd: tauri_plugin_shell::process::Command) -> Result<CommandChild, String> {
    cmd.spawn()
        .map(|(_events, child)| child)
        .map_err(|e| e.to_string())
}

fn spawn_backend(app: &tauri::AppHandle, user_data: &PathBuf, port: u16) -> Result<CommandChild, String> {
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
            ));
        }
    }

    spawn_child(sidecar_env(
        shell.sidecar("linkdapply-backend").map_err(|e| e.to_string())?,
        user_data,
        host,
        &port_str,
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
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let _ = dotenvy::from_path(manifest.join("../.env"));

    let port = api_port();
    let user_data = user_data_dir();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(move |app| {
            let handle = app.handle().clone();
            let child = spawn_backend(&handle, &user_data, port).map_err(|e| {
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

            let window = WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url.parse().unwrap()))
                .title("LinkdApply")
                .inner_size(1280.0, 860.0)
                .initialization_script(&inject)
                .build()?;

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
        .expect("error while running LinkdApply desktop");
}
