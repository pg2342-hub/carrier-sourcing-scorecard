"""Builds the synthetic shadow week in data/ (fixed seed, so every run gives the same files).

Nothing here is real: carrier names, IDs, rates and times are invented. Lane miles are rough
road distances from Irving, TX. Rates start from DAT's national dry van spot linehaul average
($2.26 per mile, week ending 2026-10-17) with a short-haul premium and noise.
"""
import csv
import random

random.seed(20261119)

# carrier_id, name, authority_status, authority_granted, auto_liability, cargo, safety_rating,
# equipment, contact_matches_registry, do_not_use, insurance_expires, quote_style
CARRIERS = [
    ("C01", "Trinity Line Haul (synthetic)", "ACTIVE", "2015-03-02", 1000000, 100000, "Satisfactory", "V", "Y", "N", "2027-06-30", "fair"),
    ("C02", "Red River Freight (synthetic)", "ACTIVE", "2019-08-15", 1000000, 250000, "None", "V|R", "Y", "N", "2027-02-28", "fair"),
    ("C03", "Brazos Transport (synthetic)", "ACTIVE", "2011-01-20", 2000000, 100000, "Satisfactory", "V", "Y", "N", "2027-04-01", "fair"),
    ("C04", "Pecos Carriers (synthetic)", "ACTIVE", "2021-05-10", 1000000, 100000, "None", "V", "Y", "N", "2027-01-15", "fair"),
    ("C05", "Cross Timbers Logistics (synthetic)", "ACTIVE", "2017-11-01", 1000000, 150000, "Satisfactory", "V|R", "Y", "N", "2027-09-30", "fair"),
    ("C06", "Lone Oak Trucking (synthetic)", "ACTIVE", "2023-02-14", 1000000, 100000, "None", "V", "Y", "N", "2027-03-31", "fair"),
    ("C07", "Caddo Lake Express (synthetic)", "ACTIVE", "2026-10-01", 1000000, 100000, "None", "V", "Y", "N", "2027-10-01", "cheap"),
    ("C08", "Sabine Road Co (synthetic)", "ACTIVE", "2018-06-30", 750000, 100000, "None", "V", "Y", "N", "2027-05-31", "cheap"),
    ("C09", "Llano Freightways (synthetic)", "INACTIVE", "2016-09-09", 1000000, 100000, "None", "V", "Y", "N", "2027-01-31", "cheap"),
    ("C10", "Gulf Plains Haulers (synthetic)", "ACTIVE", "2020-04-04", 1000000, 50000, "None", "V", "Y", "N", "2027-02-15", "cheap"),
    ("C11", "Palo Duro Lines (synthetic)", "ACTIVE", "2014-12-12", 1000000, 100000, "Conditional", "V", "Y", "N", "2027-08-31", "mid"),
    ("C12", "Big Thicket Cartage (synthetic)", "ACTIVE", "2012-07-07", 1000000, 100000, "None", "V", "N", "N", "2027-07-31", "cheap"),
    ("C13", "Blackland Freight (synthetic)", "ACTIVE", "2019-02-02", 1000000, 100000, "None", "V", "Y", "Y", "2027-03-15", "cheap"),
    ("C14", "Hill Country Reefer (synthetic)", "ACTIVE", "2016-03-03", 1000000, 100000, "Satisfactory", "R", "Y", "N", "2027-06-01", "fair"),
    ("C15", "Prairie Star Transport (synthetic)", "ACTIVE", "2018-10-10", 1000000, 100000, "None", "V", "Y", "N", "2026-11-18", "mid"),
]

LANES = [("Houston, TX", 245), ("San Antonio, TX", 275), ("Austin, TX", 195), ("Oklahoma City, OK", 205),
         ("Little Rock, AR", 320), ("Memphis, TN", 455), ("Shreveport, LA", 190), ("New Orleans, LA", 510),
         ("Kansas City, MO", 500), ("Atlanta, GA", 790), ("Denver, CO", 790), ("Phoenix, AZ", 1010),
         ("Nashville, TN", 665), ("St. Louis, MO", 640), ("El Paso, TX", 630)]
DAYS = ["2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13"]
REPS = ["Rep A", "Rep B"]
QUOTE = {"fair": (0.985, 0.03), "mid": (0.955, 0.025), "cheap": (0.90, 0.03)}


def rpm(miles):
    return 2.26 * (1 + 0.5 * max(0, (500 - miles) / 500))


def main():
    with open("data/carriers.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["carrier_id", "name", "authority_status", "authority_granted", "auto_liability", "cargo",
                    "safety_rating", "equipment", "contact_matches_registry", "do_not_use", "insurance_expires"])
        for c in CARRIERS:
            w.writerow(c[:11])

    loads, options = [], []
    for i in range(40):
        dest, miles = random.choice(LANES)
        eq = "R" if i % 10 == 7 else "V"
        rep_buy = round(miles * rpm(miles) * random.gauss(1.0, 0.04), -1)
        loads.append([f"L{i+1:03d}", "Irving, TX", dest, miles, eq, DAYS[i % 5], REPS[i % 2], rep_buy,
                      int(random.uniform(35, 190))])
        k = random.choice([0, 1, 2, 3, 3, 4]) if miles < 700 else random.choice([0, 0, 1, 2])
        for c in random.sample(CARRIERS, k):
            mu, sd = QUOTE[c[11]]
            options.append([f"L{i+1:03d}", c[0], round(rep_buy * random.gauss(mu, sd), -1),
                            int(random.uniform(4, 75))])

    with open("data/loads.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["load_id", "origin", "destination", "miles", "equipment", "pickup_date", "rep",
                    "rep_buy_rate", "rep_minutes_to_cover"])
        w.writerows(loads)
    with open("data/agent_options.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["load_id", "carrier_id", "quote", "minutes_after_post"])
        w.writerows(options)


if __name__ == "__main__":
    main()
