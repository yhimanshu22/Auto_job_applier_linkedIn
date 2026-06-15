use std::path::Path;

/// Bake `LINKDAPPLY_INTERNAL_KEY` from `desktop/.env` into release binaries at compile time.
fn inject_internal_key_from_desktop_env() {
    let env_path = Path::new(env!("CARGO_MANIFEST_DIR")).join("../.env");
    let Ok(contents) = std::fs::read_to_string(&env_path) else {
        println!(
            "cargo:warning=desktop/.env not found — set LINKDAPPLY_INTERNAL_KEY before release builds"
        );
        return;
    };

    let mut found = false;
    for line in contents.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let Some((key, raw)) = line.split_once('=') else {
            continue;
        };
        if key.trim() != "LINKDAPPLY_INTERNAL_KEY" {
            continue;
        }
        let value = raw
            .trim()
            .trim_matches('"')
            .trim_matches('\'');
        if value.is_empty() || value == "change-me-to-a-long-random-secret" {
            println!(
                "cargo:warning=LINKDAPPLY_INTERNAL_KEY in desktop/.env is unset or still the placeholder"
            );
            continue;
        }
        println!("cargo:rustc-env=LINKDAPPLY_INTERNAL_KEY={value}");
        found = true;
        break;
    }

    if !found {
        println!(
            "cargo:warning=LINKDAPPLY_INTERNAL_KEY missing in desktop/.env — cloud subscription checks in the MSI may fail"
        );
    }
}

fn main() {
    inject_internal_key_from_desktop_env();
    tauri_build::build()
}
