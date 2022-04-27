import re
import time
from pyrogram import Client, filters

import MetaTrader5 as mt5

# display data on the MetaTrader 5 package
from firestore import *

print("MetaTrader5 package author: ", mt5.__author__)
print("MetaTrader5 package version: ", mt5.__version__)

if not mt5.initialize(login=20586466, server="Deriv-Demo", password="i7GzUbg3"):
    print("initialize() failed, error code =", mt5.last_error())
    quit()
# Connect Telegram account
app = Client(
    "tg_account",
    api_id=17821682,
    api_hash="95ff2d4a2d3bb50a9ceb3404fce976ee",
    # bot_token="5138982787:AAHpx7okVcHXXVRu6t33www3sswT7bwIjgg"
)


def check_update(text, channel_id):
    take_profit = 0
    stopLoss = 0
    if re.search(r"(?i)tp(\s?)(:?)(\s?)([0-9-.]+)", text.lower()):
        print('Tp Update')
        p_check = re.findall("(?i)tp(\s?)(:?)(\s?)([0-9-.]+)", text.upper())[0]
        take_profit = float(p_check[3])
    if re.search(r"(?i)sl(\s?)(:?)(\s?)([0-9-.]+)", text.lower()):
        print('Sl Update')
        p_check = re.findall("(?i)sl(\s?)(:?)(\s?)([0-9-.]+)", text.upper())[0]
        stopLoss = float(p_check[3])
    signal = get_signal(channel_id, False)
    position = mt5.positions_get(ticket=signal['position_id'])[0]

    print(position)
    if position.tp > 0 and take_profit == 0:
        take_profit = position.tp

    if position.sl > 0 and stopLoss == 0:
        stopLoss = position.sl

    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": position.symbol,
        "volume": position.volume,
        "position": position.ticket,
        "magic": position.magic,
        "type": position.type,
        "comment": "Telegram Signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
        "deviation": 10,
    }
    if 0 < take_profit:
        request['tp'] = take_profit
    if 0 < stopLoss:
        request['sl'] = stopLoss
    result = mt5.order_send(request)
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


def prepare_order(text, channel_id, type):
    take_profit = 0
    stopLoss = 0
    marketOrder = True
    symbol = detect_symbol(text, channel_id)
    print("Simbolo detectado: "+ str(symbol))
    if not symbol:
        print("Error con el symbol")
        return False

    if type == "buy":
        entry_price = mt5.symbol_info_tick(symbol['symbol']).bid
    else:
        entry_price = mt5.symbol_info_tick(symbol['symbol']).ask
    # check if tp exist or SL
    if re.search(r"(?i)tp(\s?)(:?)(\s?)([0-9-.]+)", text):
        print('Tp present')
        p_check = re.findall("(?i)tp(\s?)(:?)(\s?)([0-9-.]+)", text.upper())[0]
        take_profit = float(p_check[3])
    if re.search(r"(?i)sl(\s?)(:?)(\s?)([0-9-.]+)", text):
        print('Sl present')
        p_check = re.findall("(?i)sl(\s?)(:?)(\s?)([0-9-.]+)", text.upper())[0]
        stopLoss = float(p_check[3])
    if re.search(r"(?i)limit(\s?)(@?)(\s?)([0-9-.]+)", text):
        print('Limit present')
        p_check = re.findall("(?i)limit(\s?)(@?)(\s?)([0-9-.]+)", text.upper())[0]
        entry_price = float(p_check[3])
        marketOrder = False

    # test the tp
    price = mt5.symbol_info_tick(symbol['symbol']).ask
    if 0 < take_profit < price and marketOrder:
        type = "sell"
        print("TP is present and is above the current price: change to short Market Order")
    if type == "sell":
        typeOrder = mt5.ORDER_TYPE_SELL
    else:
        typeOrder = mt5.ORDER_TYPE_BUY

    # prepare the order HERE WE GOOOO
    lotSize = risk_calculator(symbol['risk'], symbol['symbol'], typeOrder)
    magic_n = random.randint(1, 99999999)

    if marketOrder == False:
        if type == "sell":
            typeOrder = mt5.ORDER_TYPE_SELL_LIMIT
        else:
            typeOrder = mt5.ORDER_TYPE_BUY_LIMIT

    # request constructor
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol['symbol'],
        "volume": lotSize,
        "type": typeOrder,
        "price": entry_price,
        "deviation": 10,
        "magic": magic_n,
        "comment": "Telegram Signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    if 0 < take_profit:
        request['tp'] = take_profit
    if 0 < stopLoss:
        request['sl'] = stopLoss

    # ALL READY HERE WE GO
    result = mt5.order_send(request)
    print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol['symbol'], lotSize, entry_price,
                                                                                 10))
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
    else:
        # Save the signal information for later
        signal_data = {
            u'symbol': symbol['symbol'],
            u'active': True,
            u'channel_id': channel_id,
            u'vol': lotSize,
            u'position_id': result.order,
            u'magic': magic_n,
            u'profit': 0,
            u'create_at': datetime.timestamp(datetime.now())
        }
        print("Save all the data")
        add_signal(signal_data, str(result.order))
    return True


def send_order(message):
    channel = get_channel(message.chat.id)

    if channel:
        # test signal message
        key_words_buy = ['buy', 'long']
        key_words_sell = ['sell', 'short']
        if any(key_words_buy in message.text.lower() for key_words_buy in key_words_buy):
            print("BUY SIGNAL")
            prepare_order(message.text, message.chat.id, "buy")
            return True
        if any(key_words_sell in message.text.lower() for key_words_sell in key_words_sell):
            print("SELL SIGNAL")
            prepare_order(message.text, message.chat.id, "sell")
            return True

        print("NO signal, just text. Test if there is a open signal to close")
        close_text = ["close", "secure", "exit", "stop", "profit"]
        text_contains_close = any(close_text in message.text.lower() for close_text in close_text)
        if text_contains_close:
            symbol = detect_symbol(message.text, message.chat.id)
            if symbol:
                print("Symbol in message close this")
            signal = get_signal(message.chat.id, symbol)
            if signal:
                try:
                    position = mt5.positions_get(ticket=signal['position_id'])[0]
                    print("Order Close")
                    print("Symbol: ", position.symbol)
                    print("Profit: ", position.profit)
                    mt5.Close(position.symbol, ticket=position.ticket)
                    close_signal(signal['position_id'], position.profit)
                except:
                    print("error")
        else:
            print("looks good, there is not signals to close :) maybe an update for the signal")
            check_update(message.text, message.chat.id)

        # Just more text no a signal :(


def risk_calculator(percentage, symbol, type):
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
