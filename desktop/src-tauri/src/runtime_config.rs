use std::path::{Path, PathBuf};

use crate::production;

/// Effective config after optional dotenv files + production defaults.
#[derive(Clone)]
pub struct RuntimeConfig {
    pub dashboard_login_url: String,
    pub frontend_url: String,
    pub extra_cors_origins: String,
    pub session_url: String,
    pub cloud_api_url: String,
    pub internal_key: Option<String>,
}

fn non_empty_env(key: &str) -> Option<String> {
    std::env::var(key)
        .ok()
        .map(|v| v.trim().to_string())
        .filter(|v| !v.is_empty())
}

fn env_or(key: &str, default: &str) -> String {
    non_empty_env(key).unwrap_or_else(|| default.to_string())
}

/// Load optional overrides, then apply production defaults for anything still unset.
pub fn load(user_data: &Path) -> RuntimeConfig {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let _ = dotenvy::from_path(manifest.join("../.env"));
    let _ = dotenvy::from_path(user_data.join(".env"));

    let frontend_url = env_or("FRONTEND_URL", production::FRONTEND_URL);
    let session_url = non_empty_env("NEXTAUTH_SESSION_URL")
        .unwrap_or_else(|| format!("{}/api/auth/session", frontend_url.trim_end_matches('/')));

    let internal_key = non_empty_env("LINKDAPPLY_INTERNAL_KEY").or_else(|| {
        production::baked_internal_key().map(|k| k.to_string())
    });

    RuntimeConfig {
        dashboard_login_url: env_or("LINKDAPPLY_FRONTEND_URL", production::DASHBOARD_LOGIN_URL),
        extra_cors_origins: env_or("EXTRA_CORS_ORIGINS", production::FRONTEND_URL),
        frontend_url,
        session_url,
        cloud_api_url: env_or("CLOUD_API_URL", production::CLOUD_API_URL),
        internal_key,
    }
}

pub fn write_env_template_if_missing(user_data: &Path) {
    let example = user_data.join(".env.example");
    if example.exists() {
        return;
    }
    let body = r#"# Optional LinkdApply overrides (copy lines to .env in this folder).
# LinkedIn credentials and bot settings are saved via the dashboard UI.

# FRONTEND_URL=https://frontend-pink-phi-37.vercel.app
# CLOUD_API_URL=https://linkedapply-backend.onrender.com
# LLM_API_KEY=your-groq-or-openai-key
"#;
    let _ = std::fs::write(example, body);
}
