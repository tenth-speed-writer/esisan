import requests as rq
import db
from datetime import datetime as dt
import logging
from json.decoder import JSONDecodeError
from time import sleep

DEBUG = True

JITA = "10000002"
AMARR = "10000043"
RENS = "10000030"
DODIXIE = "10000032"
HEK = "10000042"
THERA = "11000031"

# Thera is small, so it's useful for development--but could also be a cool market candidate for study.
# Remember, Thera is a perfectly viable market if you're willing to crash a hole camp. :)
TARGET_MARKET = THERA

MARKET_REGIONS = (JITA, AMARR, RENS, DODIXIE, HEK)

API_URL = "https://esi.evetech.net/latest/"

# Type IDs of various good categories
MINERALS = [("Tritanium", 34),
            ("Pyerite", 35),
            ("Mexallon", 36),
            ("Isogen", 37),
            ("Nocxium", 38),
            ("Zydrine", 39),
            ("Megacyte", 40),
            ("Morphite", 11399)]

def _fetch_page(region_id, now, page=1):
    """Returns a list of one row dict for each outstanding buy or sell order in the specified region.
    Requires the datestamp of the query batch to be specified in format %Y-%m-%dT%H:%M:%S:%Z"""
    path = API_URL + 'markets/{}/orders/'.format(str(region_id))

    params = {
        "datasource": "tranquility",
        "order_type": "all",
        "page": str(page)
    }

    # Execute request and parse response to a list of dicts
    try:
        res = rq.get(path, params=params)
        try:
            rows = res.json()

            if rows is None:
                # Get nothing, return nothing--and dodge a bug.
                return []
            else:
                # Convert is_buy_order bool to a type string
                for r in rows:
                    r["queried_on"] = now
                    if r["is_buy_order"]:
                        r["type"] = "buy"
                    else:
                        r["type"] = "sell"
                return rows

        except JSONDecodeError as err:
            logging.error(err)
            logging.debug("\n\nMessage body reads as:\n" + res.text)
            return -1
    except rq.exceptions.ConnectionError as err:
        logging.error(err)
        print("Skipping iteration - Connection Error")
        return -1


def _flatten_order_row(r):
    """Flattening the rows isn't pretty, but it's what SQLite wants."""
    return [r["order_id"],
            r["queried_on"],
            r["location_id"],
            r["system_id"],
            r["type_id"],
            r["duration"],
            r["issued"],
            r["range"],
            r["type"],
            r["price"],
            r["volume_total"],
            r["volume_remain"],
            r["min_volume"]]


def _save_page(rows):
    """Takes a list of dicts, each of which contains data for an order on the market.
    Saves the contents into the database."""

    query = """REPLACE INTO orders
               VALUES (?,?,?,?,?,
                       ?,?,?,?,?,
                       ?,?,?)"""

    with db.make_connection() as conn:
        c = conn.cursor()
        c.executemany(query, ([_flatten_order_row(r) for r in rows]))
        conn.commit()


def update_region(region_id=TARGET_MARKET):
    now = dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")
    print("Beginning cache for region " + str(region_id) + " at " + now)

    page_no = 1
    empty_response = False
    while not empty_response:
        page = _fetch_page(region_id,
                           now=now,
                           page=page_no)
        if page == -1:
            # If the page failed to load or parse, move on to the next page.
            page_no += 1
            logging.warning("Skipping to page " + str(page_no))
            pass
        elif not page:
            # If it returned no records, set the trigger to end the loop.
            empty_response = True
            pass
        else:
            # Save the freshly-acquired page and increment the page_no.
            _save_page(page)
            page_no += 1

            if DEBUG and page_no % 5 == 0:
                print("Page " + str(page_no) + " recorded.")
            pass

    print("Update executed for region {} at {} completed at {}."
          .format(region_id,
                  now,
                  dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")))
    print(str(page_no-1) + "pages of 1,000 records processed.")


def update_minerals():
    """Updates each mineral in each market region."""
    now = dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")
    for region_id in MARKET_REGIONS:
        for type_id in [m[1] for m in MINERALS]:
            params = {
                "datasource": "tranquility",
                "order_type": "all",
                "type_id": type_id
            }
            path = API_URL + "markets/{}/orders/".format(region_id)
            res = rq.get(path, params=params)
            rows = res.json()
            for r in rows:
                r["queried_on"] = now
                r["type"] = "buy" if r["is_buy_order"] else "sell"
            _save_page(rows)
        print("Updated mineral prices for region {}".format(str(region_id)))


for i in range(0, 180):
    update_minerals()
    sleep(300)
