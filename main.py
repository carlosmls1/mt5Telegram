from datetime import datetime
import random

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
    doc_ref = db.collection(u'signal').document(id)
    doc_ref.set(data)


# Read Data
def get_channel(channel_id):
    doc_ref = db.collection(u'channels').document(channel_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return False


def get_signal(channel_id, symbol):
    doc_ref = db.collection(u'signal')

    doc_ref.where(u'symbol', u'==', symbol)
    doc_ref.where(u'channel_id', u'==', channel_id)
    doc_ref.where(u'active', u'==', True)
    docs = doc_ref.stream()
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
def close_signal(position_id, profit):
    doc_ref = db.collection(u'signal').document(position_id)
    signal = doc_ref.get().to_dict()
    signal['active'] = False
    signal['profit'] = profit
    doc_ref.set(signal)


# date
#dt = datetime.now()
#
#symbol_data = {
#    u'symbol': u'Volatility 75 Index',
#    u'risk': 1,
#    u'status': True
#}
#channel_data = {
#    u'channel_id': u'ID_TELEGRAM_2',
#    u'name': u'Demo Channer2',
#    u'signal_format': 'regex_format_here',
#    u'status': True
#}
#
#magic_n = random.randint(1,99999999)
#signal_data = {
#    u'symbol': 'Volatility 75 Index',
#    u'active': True,
#    u'channel_id': u'-1112121',
#    u'vol': 0.0001,
#    u'position_id': "12312412",
#    u'magic': magic_n,
#    u'profit': 0,
#    u'create_at': datetime.timestamp(dt)
#}
#
#add_signal(signal_data, "12312412")
#
#signal = get_signal('-1112121', 'Volatility 75 Index')
#close_signal(signal['position_id'],1000)
#