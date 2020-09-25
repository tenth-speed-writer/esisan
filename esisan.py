import requests as rq
import db
from datetime import datetime as dt

JITA = "10000002"
AMARR = "10000043"
RENS = "10000030"
DODIXIE = "10000032"
HEK = "10000042"
THERA = "11000031"

# Thera is small, so it's useful for development--but could also be a cool market candidate for study.
# Remember, Thera is a perfectly viable market if you're willing to crash a hole camp. :)
TARGET_MARKET = THERA

market_regions = (JITA, AMARR, RENS, DODIXIE, HEK)

API_URL = "https://esi.evetech.net/latest/"


def get_orders_for_region(region_id):
    """Returns a list of one row dict for each outstanding buy or sell order in the specified region."""
    path = API_URL + 'markets/{}/orders/'.format(str(region_id))
    now = dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")
    print("Beginning cache for region " + str(region_id) + " at " + now)

    def get_page(page):
        """Returns a single page of orders using the specified path."""
        params = {
            "datasource": "tranquility",
            "order_type": "all",
            "page": str(page)
        }
        res = rq.get(path, params=params)
        rows = res.json()
        for r in rows:
            if r["is_buy_order"]:
                r["type"] = "buy"
            else:
                r["type"] = "sell"
        return rows

    def get_all_pages(page_no=1,
                      pages=[]):
        """Recursively gathers and compiles order rows from ESI for the specified path.

        Returns a list of row dicts."""
        next_page = get_page(page_no)

        if len(pages) == 0:
            next_pages = next_page
        else:
            next_pages = pages + next_page

        if len(next_page) == 0:
            print("Update collected.")
            return pages
        else:
            print("Got page {} - {} records so far".format(str(page_no),
                                                           str(len(next_pages))))
            return get_all_pages(page_no + 1,
                                 next_pages)

    # Execute request sequence, appending the query timestamp before returning the rows.
    rows = get_all_pages()
    for r in rows:
        r["queried_on"] = now
    return rows


def save_orders(region_id=TARGET_MARKET):
    """Pulls live orders for the target region_id and inserts them into the database."""
    live_orders = get_orders_for_region(region_id)

    # Pretty sure SQLite can parse dicts as inputs.
    # There's a more elegant solution than this.
    flat_orders = [(o["order_id"],
                    o["queried_on"],
                    o["location_id"],
                    o["system_id"],
                    o["type_id"],
                    o["duration"],
                    o["issued"],
                    o["range"],
                    o["type"],
                    o["price"],
                    o["volume_total"],
                    o["volume_remain"],
                    o["min_volume"])
                   for o in live_orders]

    # TODO: Abstract the DB call to a method in db.py
    with db.make_connection() as conn:
        c = conn.cursor()
        query = """REPLACE INTO orders
                   VALUES (?,?,?,?,?,
                           ?,?,?,?,?,
                           ?,?,?)"""
        c.executemany(query, flat_orders)
        now = dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")
        print("Update which began at {} has completed at {}".format(live_orders[0]["queried_on"],
                                                                    now))