from datetime import datetime
import random
import re

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
cred = credentials.Certificate('./mt5telegram-cc92c244d735.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


# Add Data
def create_channel(channel, data):
    doc_ref = db.collection(u'channels').document(channel)
    doc_ref.set(data)


def add_symbol(channel_id, symbol_id, data):
    channel_ref = db.collection(u'channels').document(channel_id)
    message_ref = channel_ref.collection(u'symbols').document(symbol_id)
    message_ref.set(data)


def add_signal(data, id):
    id = str(id)
    doc_ref = db.collection(u'signal').document(id)
    doc_ref.set(data)


# Read Data
def get_channel(channel_id):
    channel_id = str(channel_id)
    doc_ref = db.collection(u'channels').document(channel_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return False


def get_pr_channel(channel_id):
    channel_id = str(channel_id)
    doc_ref = db.collection(u'channels').where(u'channel_id', u'==', channel_id)
    docs = doc_ref.get()
    for doc in docs:
        return doc.to_dict()
    return False


def get_signal(channel_id, symbol):
    doc_ref = db.collection(u'signal')
    # if symbol:
    #    doc_ref.where(u'symbol', u'==', symbol)
    if symbol:
        docs = doc_ref.where(u'channel_id', u'==', channel_id).where(u'active', u'==', True).where(u'symbol', u'==',
                                                                                                   symbol[
                                                                                                       'symbol']).stream()
        for doc in docs:
            return doc.to_dict()
        return False
    else:
        docs = doc_ref.where(u'channel_id', u'==', channel_id).where(u'active', u'==', True).stream()
        for doc in docs:
            return doc.to_dict()
        return False


def get_symbol(channel_id, symbol_id):
    doc_ref = db.collection(u'channels').document(channel_id).collection(u'symbols').document(symbol_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return False


# Utils
def detect_symbol(text, channel_id):
    print()

    doc_ref = db.collection(u'channels').document(str(channel_id)).collection(u'symbols')
    docs = doc_ref.stream()
    text = text.lower().replace("(1s)", "s1").replace("(s1)", "s1")
    for doc in docs:
        symbol = doc.id.lower().replace("(1s)", "s1").replace("(s1)", "s1")
        if re.search(""+symbol+"\b", text):
            return doc.to_dict()
        elif re.search(""+symbol+"\s", text):
            return doc.to_dict()
    return False


def close_signal(position_id, profit):
    position_id = str(position_id)
    doc_ref = db.collection(u'signal').document(position_id)
    signal = doc_ref.get().to_dict()
    signal['active'] = False
    signal['profit'] = profit
    doc_ref.set(signal)

def CopyChannel(origin_id, destination_id):
    original = get_channel(origin_id)
    channel_data = {
        u'channel_id': destination_id,
        u'name': u'SM trader vip',
        u'signal_format': original['signal_format'],
        u'status': True
    }
    create_channel(channel_data['channel_id'], channel_data)
    #Add Symbols
    doc_symbols = db.collection(u'channels').document(origin_id).collection(u'symbols')
    docs = doc_symbols.stream()
    for doc in docs:
        print(doc.id)
        symbol_data = doc.to_dict()
        add_symbol(destination_id, doc.id, symbol_data)

# date
# dt = datetime.now()
#

#number = "100"
#symbol_data = {
#    u'symbol': u'Volatility ' + str(number) + ' Index',
#    u'risk': 1,
#    u'status': True
#}
#add_symbol("-1001642622359", "V" + str(number), symbol_data)
#symbol_data = {
#    u'symbol': u'Volatility 75 Index',
#    u'risk': 1,
#    u'status': True
#}
#add_symbol("-1001642622359", "V75", symbol_data)

#channel_data = {
#  u'channel_id': u'--1001446073742',
#  u'name': u'SM trader vip',
#  u'signal_format': '(Buy|Sell)+(Step index|V75[(]1s[)]|V100[(]1s[)]|V75|V100|V75s|V100s|Boom 1000|Crash 1000)',
#  u'status': True
#}
#CopyChannel('-1001522495307', '-1001599621510')


#
# magic_n = random.randint(1,99999999)
# signal_data = {
#    u'symbol': 'Volatility 75 Index',
#    u'active': True,
#    u'channel_id': u'-1112121',
#    u'vol': 0.0001,
#    u'position_id': "12312412",
#    u'magic': magic_n,
#    u'profit': 0,
#    u'create_at': datetime.timestamp(dt)
# }
#
# add_signal(signal_data, "12312412")
#
# signal = get_signal('-1112121', 'Volatility 75 Index')
# print(signal)
# close_signal(signal['position_id'],1000)
#
# print(get_pr_channel("-1001523154403"))
