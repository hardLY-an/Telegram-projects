import asyncio
import time
from pyrogram import Client
from pyrogram.raw.functions.payments import (
    GetStarGifts,
    GetPaymentForm,
    GetStarsStatus,
    SendStarsForm
)
from pyrogram.raw.types.payments import (
    StarGiftsNotModified,
)
from pyrogram.raw.types import (
    InputInvoiceStarGift,
    InputPeerSelf,
)
from pyrogram.errors import FloodWait, UserDeactivated, AuthKeyUnregistered


# Enter details
API_ID = None
API_HASH = None
SESSION_NAME = ""

CHECK_INTERVAL_SECONDS = 30

known_gift_ids = set()
last_gift_list_hash = 0

app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)


async def get_current_star_balance():
    try:
        status = await app.invoke(GetStarsStatus(peer=InputPeerSelf()))
        return status.balance.amount
    except Exception as e:
        print(f"Error while getting stars balance: {e}")
        return 0


async def purchase_gift(gift_to_purchase):
    gift_id = gift_to_purchase.id
    gift_stars_cost = gift_to_purchase.stars

    print(f"Attempting to purchase gift ID: {gift_id} for {gift_stars_cost} stars")

    current_balance = await get_current_star_balance()

    if current_balance < gift_stars_cost:
        print(f"Not enough stars to purchase. Balance: {current_balance}, Required: {gift_stars_cost}")
        return False

    try:
        invoice_details = InputInvoiceStarGift(
            peer=InputPeerSelf(),
            gift_id=gift_id
        )

        payment_form_response = await app.invoke(
            GetPaymentForm(invoice=invoice_details)
        )
        print(f"Payment form received: ID={payment_form_response.form_id}")


        payment_result = await app.invoke(
            SendStarsForm(
                form_id=payment_form_response.form_id,
                invoice=invoice_details
            )
        )

        print(f"Gift ID {gift_id} successfully purchased!")
        return True

    except FloodWait as e:
        print(f"FloodWait while purchasing gift ID {gift_id}: waiting {e.value} seconds.")
        await asyncio.sleep(e.value + 5)
        return False
    except Exception as e:
        print(f"Error while purchasing gift ID {gift_id}: {type(e).__name__} - {e}")
        return False


async def monitor_and_buy_new_gifts():
    global known_gift_ids
    global last_gift_list_hash

    print("Starting monitoring and purchasing gifts...")

    target_gift = None

    try:
        initial_gifts_response = await app.invoke(GetStarGifts(hash=0))
        if hasattr(initial_gifts_response, 'gifts'):
            for gift in initial_gifts_response.gifts:
                known_gift_ids.add(gift.id)
                print(f"Gift ID: {gift.id}")



            last_gift_list_hash = initial_gifts_response.hash
            print(f"Initialization: {len(known_gift_ids)} gifts known. Hash: {last_gift_list_hash}")
        else:
            print(f"Initialization: received unexpected response {type(initial_gifts_response)}")

    except Exception as e:
        print(f"Critical error during gift list initialization: {e}. Exiting")
        return

    while True:
        print(f"\nChecking for new gifts... (Hash for request: {last_gift_list_hash})")
        

        print(f"{len(known_gift_ids)} gifts known")

        balance = await get_current_star_balance()
        print(f"Current balance: {balance} ★")

        new_gifts_this_cycle = []
        try:
            star_gifts_response = await app.invoke(
                GetStarGifts(hash=last_gift_list_hash)
            )

            if hasattr(star_gifts_response, 'gifts'):
                # print(f"Новий star_gifts_response: {star_gifts_response}")
                print("Changes detected in the gift list")
                for gift_data in star_gifts_response.gifts:
                    if gift_data.id not in known_gift_ids:
                        if not gift_data.sold_out:
                            print(
                                f"NEW available gift found! ID: {gift_data.id}, Name (if available): {getattr(gift_data, 'title', 'N/A')}, Stars: {gift_data.stars}")
                            new_gifts_this_cycle.append(gift_data)
                        else:
                            print(f"New but sold out gift found. ID: {gift_data.id}")
                        known_gift_ids.add(gift_data.id)

                last_gift_list_hash = star_gifts_response.hash
                print(f"Gift list updated on the server. New hash: {last_gift_list_hash}")

                for new_gift in new_gifts_this_cycle:
                    print(f"Decision made to purchase new gift ID: {new_gift.id}")
                    await purchase_gift(new_gift)
                    await asyncio.sleep(5)




            elif isinstance(star_gifts_response, StarGiftsNotModified):
                print("Gift list has not changed")
            else:
                print(f"Unexpected response from GetStarGifts: {type(star_gifts_response)}")

        except FloodWait as e:
            print(f"FloodWait in monitoring loop: waiting {e.value} seconds")
            await asyncio.sleep(e.value + 5)
        except (UserDeactivated, AuthKeyUnregistered) as e:
            print(f"Account problem ({type(e).__name__}): {e}. Exiting")
            break
        except Exception as e:
            print(f"Error in monitoring loop: {type(e).__name__} - {e}")

        print(f"Current time: {time.strftime('%H:%M:%S', time.localtime())}")
        print(f"Next check in {CHECK_INTERVAL_SECONDS} seconds")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def main():
    await app.start()
    try:
        await monitor_and_buy_new_gifts()

    finally:
        print("Shutting down the client...")
        await app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    except Exception as e:
        print(f"Unexpected top-level error: {e}")
    finally:
        print("Script finished")