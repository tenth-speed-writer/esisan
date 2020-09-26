import requests as rq
import db
from datetime import datetime as dt
import logging
from json.decoder import JSONDecodeError

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

market_regions = (JITA, AMARR, RENS, DODIXIE, HEK)

API_URL = "https://esi.evetech.net/latest/"


# def get_orders_for_region(region_id):
#     """Returns a list of one row dict for each outstanding buy or sell order in the specified region."""
#     path = API_URL + 'markets/{}/orders/'.format(str(region_id))
#     now = dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")
#     print("Beginning cache for region " + str(region_id) + " at " + now)
#
#     def get_page(page):
#         """Returns a single page of orders using the specified path."""
#         params = {
#             "datasource": "tranquility",
#             "order_type": "all",
#             "page": str(page)
#         }
#         res = rq.get(path, params=params)
#         rows = res.json()
#         for r in rows:
#             if r["is_buy_order"]:
#                 r["type"] = "buy"
#             else:
#                 r["type"] = "sell"
#         return rows
#
#     def get_all_pages(page_no=1,
#                       pages=[]):
#         """Recursively gathers and compiles order rows from ESI for the specified path.
#
#         Returns a list of row dicts."""
#         next_page = get_page(page_no)
#
#         if len(pages) == 0:
#             next_pages = next_page
#         else:
#             next_pages = pages + next_page
#
#         if len(next_page) == 0:
#             print("Update collected.")
#             return pages
#         else:
#             print("Got page {} - {} records so far".format(str(page_no),
#                                                            str(len(next_pages))))
#             return get_all_pages(page_no + 1,
#                                  next_pages)
#
#     # Execute request sequence, appending the query timestamp before returning the rows.
#     rows = get_all_pages()
#     for r in rows:
#         r["queried_on"] = now
#     return rows
#
#
# def save_orders(region_id=TARGET_MARKET):
#     """Pulls live orders for the target region_id and inserts them into the database."""
#     live_orders = get_orders_for_region(region_id)
#     flat_orders = [(o["order_id"],
#                     o["queried_on"],
#                     o["location_id"],
#                     o["system_id"],
#                     o["type_id"],
#                     o["duration"],
#                     o["issued"],
#                     o["range"],
#                     o["type"],
#                     o["price"],
#                     o["volume_total"],
#                     o["volume_remain"],
#                     o["min_volume"])
#                    for o in live_orders]
#
#     # TODO: Abstract the DB call to a method in db.py
#     with db.make_connection() as conn:
#         c = conn.cursor()
#         query = """REPLACE INTO orders
#                    VALUES (?,?,?,?,?,
#                            ?,?,?,?,?,
#                            ?,?,?)"""
#         c.executemany(query, flat_orders)
#         now = dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")
#         print("Update which began at {} has completed at {}".format(live_orders[0]["queried_on"],
#                                                                     now))

def fetch_page(region_id, now, page=1):
    """Returns a list of one row dict for each outstanding buy or sell order in the specified region.
    Requires the datestamp of the query batch to be specified in format %Y-%m-%dT%H:%M:%S:%Z"""
    path = API_URL + 'markets/{}/orders/'.format(str(region_id))

    params = {
        "datasource": "tranquility",
        "order_type": "all",
        "page": str(page)
    }

    # Execute request and parse response to a list of dicts
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


def save_page(rows):
    """Takes a list of dicts, each of which contains data for an order on the market.
    Saves the contents into the database."""
    query = """REPLACE INTO orders
               VALUES (?,?,?,?,?,
                       ?,?,?,?,?,
                       ?,?,?)"""

    with db.make_connection() as conn:
        c = conn.cursor()

        # Flattening the rows isn't pretty, but it's what SQLite wants.
        c.executemany(query, ([(r["order_id"],
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
                                r["min_volume"])
                               for r in rows]))
        conn.commit()


def update_region(region_id=TARGET_MARKET):
    now = dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")
    print("Beginning cache for region " + str(region_id) + " at " + now)

    page_no = 1
    empty_response = False
    while not empty_response:
        page = fetch_page(region_id,
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
            save_page(page)
            page_no += 1

            if DEBUG and page_no % 5 == 0:
                print("Page " + str(page_no) + " recorded.")
            pass

    print("Update executed for region {} at {} completed at {}."
          .format(region_id,
                  now,
                  dt.strftime(dt.utcnow(), "%Y-%m-%dT%H:%M:%S%Z")))
    print(str(page_no-1) + "pages of 1,000 records processed.")

update_region(JITA)