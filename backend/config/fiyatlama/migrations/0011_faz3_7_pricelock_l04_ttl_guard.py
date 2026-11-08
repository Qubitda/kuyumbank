# Dilim 3.7 L-04 — PriceLock INSERT: gecerlilik_sonu / alici_firma = Quote

from django.db import migrations


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION fiyatlama_pricelock_guard()
RETURNS trigger AS $$
DECLARE
  q_gecerlilik timestamptz;
  q_alici_id bigint;
BEGIN
  IF TG_OP = 'INSERT' THEN
    SELECT gecerlilik_sonu, alici_firma_id
      INTO q_gecerlilik, q_alici_id
      FROM fiyatlama_pricequote
     WHERE id = NEW.quote_id;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'PriceLock INSERT: PriceQuote bulunamadı (ADR-0010 L-04)';
    END IF;
    IF NEW.gecerlilik_sonu IS DISTINCT FROM q_gecerlilik THEN
      RAISE EXCEPTION
        'PriceLock INSERT: gecerlilik_sonu quote ile eşit olmalı (ADR-0010 L-04)';
    END IF;
    IF NEW.alici_firma_id IS DISTINCT FROM q_alici_id THEN
      RAISE EXCEPTION
        'PriceLock INSERT: alici_firma quote ile eşit olmalı (ADR-0010 L-04)';
    END IF;
    RETURN NEW;
  END IF;

  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'PriceLock immutable (ADR-0010); DELETE reddedildi';
  END IF;

  IF TG_OP = 'UPDATE' THEN
    IF OLD.durum = 'AKTIF'
       AND NEW.durum = 'SURESI_DOLDU'
       AND NEW.quote_id IS NOT DISTINCT FROM OLD.quote_id
       AND NEW.alici_firma_id IS NOT DISTINCT FROM OLD.alici_firma_id
       AND NEW.toplam_vergisiz IS NOT DISTINCT FROM OLD.toplam_vergisiz
       AND NEW.para_birimi IS NOT DISTINCT FROM OLD.para_birimi
       AND NEW.kilit_zamani IS NOT DISTINCT FROM OLD.kilit_zamani
       AND NEW.gecerlilik_sonu IS NOT DISTINCT FROM OLD.gecerlilik_sonu
       AND NEW.idempotency_key IS NOT DISTINCT FROM OLD.idempotency_key
       AND NEW.olusturan_id IS NOT DISTINCT FROM OLD.olusturan_id
       AND NEW.olusturma_tarihi IS NOT DISTINCT FROM OLD.olusturma_tarihi
    THEN
      RETURN NEW;
    END IF;
    RAISE EXCEPTION
      'PriceLock immutable (ADR-0010); UPDATE reddedildi (yalnız AKTIF→SURESI_DOLDU)';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pricelock_guard ON fiyatlama_pricelock;
CREATE TRIGGER trg_pricelock_guard
BEFORE INSERT OR UPDATE OR DELETE ON fiyatlama_pricelock
FOR EACH ROW EXECUTE FUNCTION fiyatlama_pricelock_guard();
"""

# 0010 durumuna geri dönüş (INSERT kontrolü yok; yalnız UPDATE/DELETE)
REVERSE_SQL = """
CREATE OR REPLACE FUNCTION fiyatlama_pricelock_guard()
RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'PriceLock immutable (ADR-0010); DELETE reddedildi';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF OLD.durum = 'AKTIF'
       AND NEW.durum = 'SURESI_DOLDU'
       AND NEW.quote_id IS NOT DISTINCT FROM OLD.quote_id
       AND NEW.alici_firma_id IS NOT DISTINCT FROM OLD.alici_firma_id
       AND NEW.toplam_vergisiz IS NOT DISTINCT FROM OLD.toplam_vergisiz
       AND NEW.para_birimi IS NOT DISTINCT FROM OLD.para_birimi
       AND NEW.kilit_zamani IS NOT DISTINCT FROM OLD.kilit_zamani
       AND NEW.gecerlilik_sonu IS NOT DISTINCT FROM OLD.gecerlilik_sonu
       AND NEW.idempotency_key IS NOT DISTINCT FROM OLD.idempotency_key
       AND NEW.olusturan_id IS NOT DISTINCT FROM OLD.olusturan_id
       AND NEW.olusturma_tarihi IS NOT DISTINCT FROM OLD.olusturma_tarihi
    THEN
      RETURN NEW;
    END IF;
    RAISE EXCEPTION
      'PriceLock immutable (ADR-0010); UPDATE reddedildi (yalnız AKTIF→SURESI_DOLDU)';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pricelock_guard ON fiyatlama_pricelock;
CREATE TRIGGER trg_pricelock_guard
BEFORE UPDATE OR DELETE ON fiyatlama_pricelock
FOR EACH ROW EXECUTE FUNCTION fiyatlama_pricelock_guard();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("fiyatlama", "0010_faz3_7_price_lock"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
    ]
