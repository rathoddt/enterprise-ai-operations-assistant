import asyncio


async def fetch_documents():
    await asyncio.sleep(2)
    return "Documents retrieved"


async def fetch_customer():
    await asyncio.sleep(2)
    return "Customer retrieved"


async def fetch_payment():
    await asyncio.sleep(2)
    return "Payment retrieved"

# Sequential execution
# async def main():

#     documents = await fetch_documents()
#     customer = await fetch_customer()
#     payment = await fetch_payment()

#     print(documents)
#     print(customer)
#     print(payment)

# Concurrent execution using asyncio.gather
async def main():

    results = await asyncio.gather(
        fetch_documents(),
        fetch_customer(),
        fetch_payment()
    )

    for result in results:
        print(result)


asyncio.run(main())
