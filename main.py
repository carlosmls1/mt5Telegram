import re
from pyrogram import Client, filters

import MetaTrader5 as mt5

print("MetaTrader5 package author: ", mt5.__author__)
print("MetaTrader5 package version: ", mt5.__version__)

if not mt5.initialize(login=1051272726, server="FTMO-Demo", password="HH1AJWDGFC"):
    print("initialize() failed, error code =", mt5.last_error())
    quit()
# Connect Telegram account
app = Client(
    "tg_account",
    api_id=17821682,
    api_hash="95ff2d4a2d3bb50a9ceb3404fce976ee",
    # bot_token="5138982787:AAHpx7okVcHXXVRu6t33www3sswT7bwIjgg"
)
risk = 1


def get_symbol(text):
    symbols = mt5.symbols_get()
    for s in symbols:
        if s.name.lower() in text.lower():
            return s
    return None


def order_type(text):
    text = text.lower()
    key_words_buy = ['buy', 'long']
    key_words_sell = ['sell', 'short']
    limit = False
    stop = False
    if 'limit' in text:
        limit = True
    if 'buy stop' in text:
        stop = True
    if 'sell stop' in text:
        stop = True

    if any(key_words_buy in text for key_words_buy in key_words_buy):
        if limit:
            return mt5.ORDER_TYPE_BUY_LIMIT
        if stop:
            return mt5.ORDER_TYPE_BUY_STOP
        return mt5.ORDER_TYPE_BUY

    if any(key_words_sell in text for key_words_sell in key_words_sell):
        if limit:
            return mt5.ORDER_TYPE_SELL_LIMIT
        if stop:
            return mt5.ORDER_TYPE_SELL_STOP
        return mt5.ORDER_TYPE_SELL


def get_prices(text, type):
    if type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_BUY]:
        type = 'buy'

    if type in [mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_SELL_STOP, mt5.ORDER_TYPE_SELL]:
        type = 'sell'

    order_prices = {
        'stop_loss': 0,
        'entry_price': 0,
        'take_profit': 0
    }
    prices_order = {
        'lowest_price': 0,
        'entry_price': 0,
        'highest_price': 0
    }
    if re.search(r"([0-9-.]+)", text):
        prices = re.findall("([0-9-.]+)", text.upper())
        prices = [float(x) for x in prices]
        prices.sort()
        prices_order['lowest_price'] = float(prices[0])
        prices_order['entry_price'] = float(prices[1])
        prices_order['highest_price'] = float(prices[2])

        if type == 'buy':
            order_prices['entry_price'] = prices_order['entry_price']
            order_prices['take_profit'] = prices_order['highest_price']
            order_prices['stop_loss'] = prices_order['lowest_price']
        if type == 'sell':
            order_prices['entry_price'] = prices_order['entry_price']
            order_prices['take_profit'] = prices_order['lowest_price']
            order_prices['stop_loss'] = prices_order['highest_price']
        return order_prices
    return False


def request(symbol, typeOrder, price):
    lotSize = risk_calculator(risk, symbol.name, typeOrder)
    print(typeOrder)
    if typeOrder == mt5.ORDER_TYPE_BUY:

        price['entry_price'] = mt5.symbol_info_tick(symbol.name).bid
    if typeOrder == mt5.ORDER_TYPE_SELL:
        price['entry_price'] = mt5.symbol_info_tick(symbol.name).ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol.name,
        "volume": lotSize,
        "type": typeOrder,
        "price": price['entry_price'],
        "tp": price['take_profit'],
        "sl": price['stop_loss'],

        "deviation": 100,
        "magic": 124578,
        "comment": "Python ML Signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    # ALL READY HERE WE GO
    result = mt5.order_send(request)
    print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol.name, lotSize,
                                                                                 price['entry_price'], 10))
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("2. order_send failed, retcode={}".format(result.retcode))
        # request the result as a dictionary and display it element by element
        result_dict = result._asdict()
        for field in result_dict.keys():
            print("   {}={}".format(field, result_dict[field]))
            # if this is a trading request structure, display it element by element as well
            if field == "request":
                traderequest_dict = result_dict[field]._asdict()
                for tradereq_filed in traderequest_dict:
                    print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))


def send_order(message):
    channel = message.chat.id
    text = message.text
    symbol = None
    if channel in [-1001719528505, -1001503458977, -1001225381314]:
        symbol = get_symbol(text)
        if symbol is not None:
            type = order_type(text)
            prices = get_prices(text, type)
            request(symbol, type, prices)

    return False


def risk_calculator(percentage, symbol, type):
    if type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_BUY]:
        type = mt5.ORDER_TYPE_BUY

    if type in [mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_SELL_STOP, mt5.ORDER_TYPE_SELL]:
        type = mt5.ORDER_TYPE_BUY

    balance = mt5.account_info().equity
    risk = float(percentage) * balance / 100
    symbol_info = mt5.symbol_info(symbol)
    ask = mt5.symbol_info_tick(symbol).ask
    margin = mt5.order_calc_margin(type, symbol, 1, ask)
    decimals = str(symbol_info.volume_step)[::-1].find('.')
    lot = round(risk / margin, decimals)
    if lot < symbol_info.volume_min:
        lot = symbol_info.volume_min
    if lot > symbol_info.volume_max:
        lot = symbol_info.volume_max
    return lot


def close_order(position_id):
    print(position_id)


@app.on_message(filters.text)
async def echo(client, message):
    send_order(message)


app.run()  # Automatically start() and idle()
