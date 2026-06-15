//! Production URLs baked into release MSIs (public endpoints).
//! Override at runtime via `%LOCALAPPDATA%\\LinkdApply\\.env` or `desktop/.env` when developing.

pub const FRONTEND_URL: &str = "https://frontend-pink-phi-37.vercel.app";
pub const CLOUD_API_URL: &str = "https://linkedapply-backend.onrender.com";
pub const DASHBOARD_LOGIN_URL: &str =
    "https://frontend-pink-phi-37.vercel.app/login?desktop=1&callbackUrl=%2Fdashboard%3Fdesktop%3D1";

/// Set at MSI build time from `desktop/.env` → `LINKDAPPLY_INTERNAL_KEY` (see `build.rs`).
pub fn baked_internal_key() -> Option<&'static str> {
    option_env!("LINKDAPPLY_INTERNAL_KEY").filter(|k| !k.is_empty())
}
