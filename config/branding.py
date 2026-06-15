import json
from pathlib import Path


DEFAULT_BRAND = {
    "company_name": "Jonathz SmartHomes Limited",
    "tagline": "Unified control for every connected room",
    "contact": {
        "email": "support@jonathz-smarthomes.local",
        "phone": "+234 000 000 0000",
        "address": "Lagos, Nigeria",
    },
    "support": {
        "help_url": "#",
        "privacy_url": "#",
        "terms_url": "#",
    },
    "theme": {
        "primary": "#0F294A",
        "secondary": "#0B0C10",
        "accent": "#D4AF37",
    },
    "assets": {
        "logo": "",
        "hero": "",
    },
}


def _first_present(*values):
    for value in values:
        if value:
            return value
    return None


def _normalize_hex(value, fallback):
    if not isinstance(value, str):
        return fallback
    value = value.strip()
    if len(value) in {4, 7} and value.startswith("#"):
        return value
    return fallback


def load_brand_config(static_folder):
    branding_dir = Path(static_folder) / "img" / "branding"
    config_path = branding_dir / "brand-config.json"
    raw = {}

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as config_file:
            raw = json.load(config_file)

    theme = raw.get("theme", raw.get("colors", {}))
    contact = raw.get("contact", raw.get("contact_info", {}))
    support = raw.get("support", raw.get("support_links", {}))
    assets = raw.get("assets", {})

    company_name = _first_present(
        raw.get("company_name"),
        raw.get("companyName"),
        raw.get("name"),
        DEFAULT_BRAND["company_name"],
    )

    logo = _first_present(
        assets.get("logo"),
        raw.get("logo"),
        _find_asset(branding_dir, ("logo", "brand")),
        DEFAULT_BRAND["assets"]["logo"],
    )
    hero = _first_present(
        assets.get("hero"),
        assets.get("hero_image"),
        raw.get("hero"),
        _find_asset(branding_dir, ("hero", "cover", "banner")),
        DEFAULT_BRAND["assets"]["hero"],
    )

    return {
        "company_name": company_name,
        "tagline": raw.get("tagline", DEFAULT_BRAND["tagline"]),
        "contact": {
            "email": contact.get("email", DEFAULT_BRAND["contact"]["email"]),
            "phone": contact.get("phone", DEFAULT_BRAND["contact"]["phone"]),
            "address": contact.get("address", DEFAULT_BRAND["contact"]["address"]),
        },
        "support": {
            "help_url": support.get("help_url", support.get("help", DEFAULT_BRAND["support"]["help_url"])),
            "privacy_url": support.get("privacy_url", support.get("privacy", DEFAULT_BRAND["support"]["privacy_url"])),
            "terms_url": support.get("terms_url", support.get("terms", DEFAULT_BRAND["support"]["terms_url"])),
        },
        "theme": {
            "primary": _normalize_hex(
                _first_present(theme.get("primary"), theme.get("primary_color"), theme.get("Primary")),
                DEFAULT_BRAND["theme"]["primary"],
            ),
            "secondary": _normalize_hex(
                _first_present(theme.get("secondary"), theme.get("secondary_color"), theme.get("Secondary")),
                DEFAULT_BRAND["theme"]["secondary"],
            ),
            "accent": _normalize_hex(
                _first_present(theme.get("accent"), theme.get("accent_color"), theme.get("Accent")),
                DEFAULT_BRAND["theme"]["accent"],
            ),
        },
        "assets": {
            "logo": _asset_url(logo),
            "hero": _asset_url(hero),
        },
    }


def _find_asset(directory, keywords):
    if not directory.exists():
        return ""
    for path in directory.iterdir():
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            continue
        lowered = path.name.lower()
        if any(keyword in lowered for keyword in keywords):
            return path.name
    return ""


def _asset_url(value):
    if not value:
        return ""
    if value.startswith(("http://", "https://", "/static/")):
        return value
    return f"/static/img/branding/{value}"
