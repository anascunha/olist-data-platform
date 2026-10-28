"""
Fase 3 — Gerador de um CRM genérico com dados fictícios.

O CRM simula a ferramenta do time comercial/marketing (estilo HubSpot/Salesforce) e é
ligado aos clientes reais do marketplace pelo `customer_unique_id` do Olist:

    owners      ← vendedores/analistas responsáveis pelos contatos
    campaigns   ← campanhas de marketing que originaram os contatos
    contacts    ← contatos do CRM (parte deles é cliente do Olist, parte é só lead)
    activities  ← interações registradas (e-mail, ligação, WhatsApp, reunião)

Características propositais para exercitar a camada Silver:
  * ~2% de contatos duplicados (mesmo contact_id, versão mais antiga em updated_at);
  * e-mails com espaços/maiúsculas e telefones em formatos variados;
  * lifecycle_stage desatualizado (contatos que já compram mas seguem como "lead").

Tudo é determinístico a partir de `--seed`. Uso:

    python -m pipelines.generate_crm                       # gera e envia ao Volume
    python -m pipelines.generate_crm --skip-upload         # apenas data/landing/crm/
"""

import argparse
import csv
import random
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

from pipelines.config import volume_path
from pipelines.download_data import upload_to_volume

OLIST_DIR = Path("data/landing/olist")
OUTPUT_DIR = Path("data/landing/crm")

CRM_START = datetime(2016, 1, 1)
CRM_END = datetime(2018, 10, 17)  # último pedido do dataset Olist

TEAMS = ["Inside Sales", "Key Accounts", "Customer Success"]
REGIONS = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
CHANNELS = ["email", "paid_search", "social_ads", "influencer", "event", "referral_program"]
CAMPAIGN_THEMES = {
    1: "Liquida Verão", 2: "Volta às Aulas", 3: "Semana do Consumidor", 4: "Páscoa",
    5: "Dia das Mães", 6: "Dia dos Namorados", 7: "Liquida Inverno", 8: "Dia dos Pais",
    9: "Aniversário Marketplace", 10: "Dia das Crianças", 11: "Black Friday", 12: "Natal",
}
CAMPAIGN_ATTRIBUTION_DAYS = 90  # contato é atribuído a campanhas iniciadas até 90 dias antes
LEAD_SOURCES_WITHOUT_CAMPAIGN = ["organic_search", "direct", "marketplace_signup"]
ACTIVITY_TYPES = ["email", "call", "whatsapp", "meeting", "note"]
ACTIVITY_OUTCOMES = ["completed", "no_answer", "positive", "negative", "scheduled"]

# lifecycle_stage: quem compra no marketplace vs. quem só existe no CRM
STAGES_MATCHED = (["customer", "opportunity", "lead", "churned"], [70, 12, 12, 6])
STAGES_UNMATCHED = (["lead", "mql", "opportunity", "disqualified"], [55, 20, 15, 10])

OWNER_COLUMNS = ["owner_id", "owner_name", "owner_email", "team", "region", "hired_at", "is_active"]
CAMPAIGN_COLUMNS = [
    "campaign_id", "campaign_name", "channel", "start_date", "end_date", "budget_brl",
]
CONTACT_COLUMNS = [
    "contact_id", "customer_unique_id", "first_name", "last_name", "email", "phone",
    "birth_date", "city", "state", "lifecycle_stage", "lead_source", "campaign_id",
    "owner_id", "marketing_opt_in", "created_at", "updated_at",
]
ACTIVITY_COLUMNS = [
    "activity_id", "contact_id", "owner_id", "activity_type", "direction", "activity_at",
    "outcome", "duration_minutes",
]


# ---------------------------------------------------------------------------
# Leitura do Olist
# ---------------------------------------------------------------------------


def load_olist_customers(olist_dir=OLIST_DIR):
    """
    Retorna {customer_unique_id: {"city", "state", "first_purchase", "orders"}} a partir dos
    CSVs de customers e orders do Olist.
    """
    olist_dir = Path(olist_dir)
    customer_to_unique = {}
    profiles = {}
    with open(olist_dir / "olist_customers_dataset.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uid = row["customer_unique_id"]
            customer_to_unique[row["customer_id"]] = uid
            profiles.setdefault(uid, {
                "city": row["customer_city"],
                "state": row["customer_state"],
                "first_purchase": None,
                "orders": 0,
            })

    with open(olist_dir / "olist_orders_dataset.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uid = customer_to_unique.get(row["customer_id"])
            if uid is None or not row["order_purchase_timestamp"]:
                continue
            purchased_at = datetime.fromisoformat(row["order_purchase_timestamp"])
            profile = profiles[uid]
            profile["orders"] += 1
            if profile["first_purchase"] is None or purchased_at < profile["first_purchase"]:
                profile["first_purchase"] = purchased_at

    return {uid: p for uid, p in profiles.items() if p["first_purchase"] is not None}


def select_matched_customers(profiles, n, rng, repeat_share=0.08):
    """
    Escolhe os customer_unique_id que existirão no CRM. Recompradores são sobre-representados
    (`repeat_share`), já que o CRM tende a concentrar clientes mais engajados — no Olist
    apenas ~3% dos clientes compram mais de uma vez.
    """
    repeat = sorted(uid for uid, p in profiles.items() if p["orders"] > 1)
    single = sorted(uid for uid, p in profiles.items() if p["orders"] == 1)
    n = min(n, len(profiles))
    n_repeat = min(len(repeat), int(n * repeat_share))
    chosen = rng.sample(repeat, n_repeat) + rng.sample(single, min(len(single), n - n_repeat))
    rng.shuffle(chosen)
    return chosen


# ---------------------------------------------------------------------------
# Geração
# ---------------------------------------------------------------------------


def _random_datetime(rng, start, end):
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, max(seconds, 0)))


def _clamp(value, start=CRM_START, end=CRM_END):
    return max(start, min(end, value))


def _slug(text):
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "".join(ch for ch in ascii_text.lower() if ch.isalnum())


def _fmt(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return value


def generate_owners(fake, rng, n=12):
    owners = []
    for i in range(1, n + 1):
        first, last = fake.first_name(), fake.last_name()
        owners.append({
            "owner_id": f"OWN-{i:03d}",
            "owner_name": f"{first} {last}",
            "owner_email": f"{_slug(first)}.{_slug(last)}@crm-exemplo.com.br",
            "team": TEAMS[(i - 1) % len(TEAMS)],
            "region": rng.choice(REGIONS),
            "hired_at": _random_datetime(rng, datetime(2014, 1, 1), datetime(2017, 6, 30)).date(),
            "is_active": "true" if rng.random() > 0.15 else "false",
        })
    return owners


def generate_campaigns(rng, first_month=date(2016, 1, 1), last_month=date(2018, 8, 1)):
    """Uma campanha sazonal por mês, com tema coerente com o calendário do varejo."""
    campaigns = []
    month, i = first_month, 1
    while month <= last_month:
        start = month + timedelta(days=rng.randint(0, 20))
        channel = rng.choice(CHANNELS)
        campaigns.append({
            "campaign_id": f"CMP-{i:04d}",
            "campaign_name": f"{CAMPAIGN_THEMES[start.month]} {start.year} - {channel}",
            "channel": channel,
            "start_date": start,
            "end_date": start + timedelta(days=rng.randint(7, 45)),
            "budget_brl": f"{rng.randint(5, 120) * 1000:.2f}",
        })
        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)
        i += 1
    return campaigns


def _pick_campaign(rng, campaigns, created):
    """Campanha iniciada até CAMPAIGN_ATTRIBUTION_DAYS antes da criação do contato (ou None)."""
    window_start = created.date() - timedelta(days=CAMPAIGN_ATTRIBUTION_DAYS)
    eligible = [c for c in campaigns if window_start <= c["start_date"] <= created.date()]
    return rng.choice(eligible) if eligible else None


def _messy_email(rng, email):
    roll = rng.random()
    if roll < 0.03:
        return f"  {email.upper()} "
    if roll < 0.05:
        return email.capitalize()
    if roll < 0.06:
        return ""
    return email


def _phone(fake, rng):
    digits = "".join(ch for ch in fake.cellphone_number() if ch.isdigit())[-11:]
    style = rng.random()
    if style < 0.5:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if style < 0.8:
        return f"+55{digits}"
    return digits


def generate_contacts(fake, rng, profiles, matched_ids, n_unmatched, owners, campaigns):
    contacts = []
    owner_ids = [o["owner_id"] for o in owners]
    olist_cities = sorted({(p["city"], p["state"]) for p in profiles.values()})

    def build(idx, uid):
        first, last = fake.first_name(), fake.last_name()
        if uid:
            profile = profiles[uid]
            city, state = profile["city"], profile["state"]
            # 75% entram no CRM antes da 1ª compra (lead convertido); 25% depois (pós-venda)
            if rng.random() < 0.75:
                created = profile["first_purchase"] - timedelta(days=rng.randint(0, 240))
            else:
                created = profile["first_purchase"] + timedelta(days=rng.randint(1, 200))
            stages, weights = STAGES_MATCHED
        else:
            city, state = rng.choice(olist_cities)
            created = _random_datetime(rng, datetime(2016, 6, 1), datetime(2018, 9, 30))
            stages, weights = STAGES_UNMATCHED

        created = _clamp(created.replace(microsecond=0))
        updated = _clamp(created + timedelta(days=rng.randint(0, 300), hours=rng.randint(0, 23)))

        campaign = _pick_campaign(rng, campaigns, created) if rng.random() < 0.7 else None
        if campaign:
            lead_source, campaign_id = campaign["channel"], campaign["campaign_id"]
        else:
            lead_source, campaign_id = rng.choice(LEAD_SOURCES_WITHOUT_CAMPAIGN), ""

        domain = rng.choice(["gmail.com", "hotmail.com", "yahoo.com.br", "outlook.com", "uol.com.br"])
        email = f"{_slug(first)}.{_slug(last)}{rng.randint(1, 999)}@{domain}"

        return {
            "contact_id": f"CRM-{idx:06d}",
            "customer_unique_id": uid or "",
            "first_name": first,
            "last_name": last,
            "email": _messy_email(rng, email),
            "phone": _phone(fake, rng),
            "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=75),
            "city": city,
            "state": state,
            "lifecycle_stage": rng.choices(stages, weights)[0],
            "lead_source": lead_source,
            "campaign_id": campaign_id,
            "owner_id": rng.choice(owner_ids),
            "marketing_opt_in": rng.choice(["true", "true", "true", "false"]),
            "created_at": created,
            "updated_at": updated,
        }

    ids = list(matched_ids) + [None] * n_unmatched
    rng.shuffle(ids)
    for idx, uid in enumerate(ids, start=1):
        contacts.append(build(idx, uid))

    # Duplicidades: versão antiga do mesmo contato, exportada com estágio anterior
    duplicates = []
    for contact in rng.sample(contacts, int(len(contacts) * 0.02)):
        older = dict(contact)
        older["updated_at"] = contact["created_at"]
        older["lifecycle_stage"] = "lead"
        duplicates.append(older)

    return contacts + duplicates


def generate_activities(rng, contacts, owners):
    activities = []
    owner_ids = [o["owner_id"] for o in owners]
    seen = set()
    for contact in contacts:
        if contact["contact_id"] in seen:  # não gera atividades para a linha duplicada
            continue
        seen.add(contact["contact_id"])

        weight = 2.5 if contact["lifecycle_stage"] in ("customer", "opportunity") else 1.2
        n = min(12, int(rng.expovariate(1 / weight)))
        for _ in range(n):
            activity_type = rng.choice(ACTIVITY_TYPES)
            end = min(CRM_END, contact["created_at"] + timedelta(days=365))
            activities.append({
                "activity_id": "",
                "contact_id": contact["contact_id"],
                "owner_id": contact["owner_id"] if rng.random() < 0.85 else rng.choice(owner_ids),
                "activity_type": activity_type,
                "direction": "inbound" if rng.random() < 0.3 else "outbound",
                "activity_at": _random_datetime(rng, contact["created_at"], end),
                "outcome": rng.choice(ACTIVITY_OUTCOMES),
                "duration_minutes": (
                    rng.randint(2, 60) if activity_type in ("call", "meeting") else ""
                ),
            })

    activities.sort(key=lambda a: (a["activity_at"], a["contact_id"]))
    for i, activity in enumerate(activities, start=1):
        activity["activity_id"] = f"ACT-{i:07d}"
    return activities


def generate_crm(profiles, n_contacts=20000, match_rate=0.75, seed=42):
    """Gera todas as tabelas do CRM. Retorna {nome_tabela: (colunas, linhas)}."""
    rng = random.Random(seed)
    fake = Faker("pt_BR")
    fake.seed_instance(seed)

    n_matched = int(n_contacts * match_rate)
    matched_ids = select_matched_customers(profiles, n_matched, rng)
    n_unmatched = n_contacts - len(matched_ids)

    owners = generate_owners(fake, rng)
    campaigns = generate_campaigns(rng)
    contacts = generate_contacts(fake, rng, profiles, matched_ids, n_unmatched, owners, campaigns)
    activities = generate_activities(rng, contacts, owners)

    return {
        "owners": (OWNER_COLUMNS, owners),
        "campaigns": (CAMPAIGN_COLUMNS, campaigns),
        "contacts": (CONTACT_COLUMNS, contacts),
        "activities": (ACTIVITY_COLUMNS, activities),
    }


def write_tables(tables, output_dir=OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, (columns, rows) in tables.items():
        path = output_dir / f"crm_{name}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: _fmt(v) for k, v in row.items()})
        print(f"📝 {path} ({len(rows):,} linhas)")
        paths.append(path)
    return paths


def summarize(tables):
    contacts = tables["contacts"][1]
    unique = {c["contact_id"]: c for c in contacts}
    matched = sum(1 for c in unique.values() if c["customer_unique_id"])
    by_stage = defaultdict(int)
    for c in unique.values():
        by_stage[c["lifecycle_stage"]] += 1
    print(f"\n👥 Contatos únicos: {len(unique):,} | duplicados: {len(contacts) - len(unique):,}")
    print(f"🔗 Ligados ao Olist (customer_unique_id): {matched:,} ({matched / len(unique):.0%})")
    print("📊 Estágios: " + ", ".join(f"{k}={v:,}" for k, v in sorted(by_stage.items())))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gera o CRM fictício ligado ao Olist")
    parser.add_argument("--olist-dir", default=str(OLIST_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--contacts", type=int, default=20000)
    parser.add_argument("--match-rate", type=float, default=0.75)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-upload", action="store_true")
    args = parser.parse_args(argv)

    print("🚀 Gerando CRM fictício (Fase 3)")
    profiles = load_olist_customers(args.olist_dir)
    print(f"🛒 {len(profiles):,} clientes únicos com pedidos no Olist")

    tables = generate_crm(profiles, args.contacts, args.match_rate, args.seed)
    write_tables(tables, args.output_dir)
    summarize(tables)

    if not args.skip_upload and not upload_to_volume(args.output_dir, volume_path("crm")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
