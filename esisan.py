import requests as rq
import db
from datetime import datetime as dt

JITA = "10000002"
AMARR = "10000043"
RENS = "10000030"
DODIXIE = "10000032"
HEK = "10000042"
THERA = "11000031"

TARGET_MARKET = THERA

market_regions = (JITA, AMARR, RENS, DODIXIE, HEK)

API_URL = "https://esi.evetech.net/latest/"


def get_orders_for_region(region_id):
    path = API_URL + 'markets/{}/orders/'.format(str(region_id))
    now = dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")
    print("Beginning cache for region " + str(region_id) + " at " + now)
    def get_page(page):
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


        # if next_page is not []:
        #     if pages is None:
        #         next_pages = next_page
        #     else:
        #         next_pages = pages + next_page
        #     print(len(next_pages))
        #     return get_all_pages(page_no + 1, next_pages)
        # else:
        #     print(len(pages))
        #     return pages

    rows = get_all_pages()
    for r in rows:
        r["queried_on"] = now
    return rows


live_orders = get_orders_for_region(TARGET_MARKET)
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