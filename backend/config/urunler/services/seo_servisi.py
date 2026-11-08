"""SEO teknik fallback (K-015). Pazarlama metni üretmez."""

from django.conf import settings


def platform_brand_name() -> str:
    return (getattr(settings, "PLATFORM_BRAND_NAME", "") or "").strip()


def teknik_baslik(ad: str, *, max_len: int) -> str:
    """Boş SEO başlığı için güvenli teknik fallback."""
    ad = (ad or "").strip()
    if not ad:
        return ""
    brand = platform_brand_name()
    text = f"{ad} | {brand}" if brand else ad
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def teknik_aciklama_kirp(metin: str, *, max_len: int = 160) -> str:
    """Var olan açıklamayı kısaltır; yoksa boş bırakır (pazarlama uydurmaz)."""
    temiz = (metin or "").replace("\n", " ").replace("\r", " ").strip()
    if not temiz:
        return ""
    if len(temiz) > max_len:
        return temiz[: max_len - 3] + "..."
    return temiz
