import asyncio
import traceback


def fire_and_forget(coro):
    if not asyncio.iscoroutine(coro):
        raise ValueError('The passed argument is not a coroutine')

    async def wrapper_coro():
        try:
            result = await coro
        except Exception as e:
            print(traceback.format_exc())

    asyncio.ensure_future(wrapper_coro())
