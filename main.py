#!/usr/bin/python
"""
Copyright 2015, Fernanda Monteiro <crie.fernanda@gmail.com>

Based on ManaMarket (tradeybot) code
Copyright 2011, Dipesh Amin <yaypunkrock@gmail.com>
Copyright 2011, Stefan Beller <stefanbeller@googlemail.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

Additionally to the GPL, you are *strongly* encouraged to share any modifications
you do on these sources.
"""

import logging
import logging.handlers
import socket
import sys
import time
import string

try:
    import config
except:
    print "no config file found. please move config.py.template to config.py and edit to your needs!"
    sys.exit(0);

from net.packet import *
from net.protocol import *
from net.packet_out import *
import utils

shop_broadcaster = utils.Broadcast()
trader_state = utils.TraderState()
logger = logging.getLogger('ManaLogger')

# global bot variables based on former Player class
EXP = 0
MONEY = 0
WEIGHT = 0
MaxWEIGHT = 0
botname = 0
botid = 0
botsex = 0
playername = 0
coord_map = 0
coord_x = 0
coord_y = 0
coord_dir = 0

def process_whisper(nick, msg, mapserv):
    msg = filter(lambda x: x in utils.allowed_chars, msg)
    if len(msg) == 0:
        return

    # Infinite chat loop anyone?
    if nick == "guild":
        return

def main():
    # Use rotating log files.
    log_handler = logging.handlers.RotatingFileHandler('activity.log', maxBytes=1048576*3, backupCount=5)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    logger.info("Bot Started.")

    account = config.account
    password = config.password
    character = config.character

    login = socket.socket()
    login.connect((config.server, config.port))
    logger.info("Login connected")

    login_packet = PacketOut(0x0064)
    login_packet.write_int32(0)
    login_packet.write_string(account, 24)
    login_packet.write_string(password, 24)
    login_packet.write_int8(0x03);
    login.sendall(str(login_packet))

    pb = PacketBuffer()
    id1 = accid = id2 = 0
    charip = ""
    charport = 0
    # Login server packet loop.
    while True:
        data = login.recv(1500)
        if not data:
            break
        pb.feed(data)
        for packet in pb:
            if packet.is_type(SMSG_LOGIN_DATA): # login succeeded
                packet.skip(2)
                id1 = packet.read_int32()
                accid = packet.read_int32()
                id2 = packet.read_int32()
                packet.skip(30)
                botsex = packet.read_int8()
                charip = utils.parse_ip(packet.read_int32())
                charport = packet.read_int16()
                login.close()
                break
        if charip:
            break

    assert charport

    char = socket.socket()
    char.connect((charip, charport))
    logger.info("Char connected")
    char_serv_packet = PacketOut(CMSG_CHAR_SERVER_CONNECT)
    char_serv_packet.write_int32(accid)
    char_serv_packet.write_int32(id1)
    char_serv_packet.write_int32(id2)
    char_serv_packet.write_int16(0)
    char_serv_packet.write_int8(player_node.sex)
    char.sendall(str(char_serv_packet))
    char.recv(4)

    pb = PacketBuffer()
    mapip = ""
    mapport = 0
    # Character Server Packet loop.
    while True:
        data = char.recv(1500)
        if not data:
            break
        pb.feed(data)
        for packet in pb:
            if packet.is_type(SMSG_CHAR_LOGIN):
                packet.skip(2)
                slots = packet.read_int16()
                packet.skip(18)
                count = (len(packet.data)-22) / 106
                for i in range(count):
                    botid = packet.read_int32()
                    EXP = packet.read_int32()
                    MONEY = packet.read_int32()
                    packet.skip(62)
                    botname = packet.read_string(24)
                    packet.skip(6)
                    slot = packet.read_int8()
                    packet.skip(1)
                    logger.info("Character information recieved:")
                    logger.info("Name: %s, Id: %s, EXP: %s, MONEY: %s", \
                    botname, botid, EXP, MONEY)
                    if slot == character:
                        break

                char_select_packet = PacketOut(CMSG_CHAR_SELECT)
                char_select_packet.write_int8(character)
                char.sendall(str(char_select_packet))

            elif packet.is_type(SMSG_CHAR_MAP_INFO):
                botid = packet.read_int32()
                coord_map = packet.read_string(16)
                mapip = utils.parse_ip(packet.read_int32())
                mapport = packet.read_int16()
                # char.close()
                break
        if mapip:
            break

    assert mapport

    mapserv = socket.socket()
    mapserv.connect((mapip, mapport))
    logger.info("Map connected")
    mapserv_login_packet = PacketOut(CMSG_MAP_SERVER_CONNECT)
    mapserv_login_packet.write_int32(accid)
    mapserv_login_packet.write_int32(botid)
    mapserv_login_packet.write_int32(id1)
    mapserv_login_packet.write_int32(id2)
    mapserv_login_packet.write_int8(botsex)
    mapserv.sendall(str(mapserv_login_packet))
    mapserv.recv(4)

    pb = PacketBuffer()
    shop_broadcaster.mapserv = mapserv
    # Map server packet loop

    print "Entering map packet loop\n";
    while True:
        data = mapserv.recv(2048)
        if not data:
            break
        pb.feed(data)

        # For unfinished trades - one way to distrupt service would be leaving a trade active.
        if trader_state.Trading.test():
            if time.time() - trader_state.timer > 2*60:
                logger.info("Trade Cancelled - Timeout.")
                trader_state.timer = time.time()
                mapserv.sendall(str(PacketOut(CMSG_TRADE_CANCEL_REQUEST)))

        for packet in pb:
            if packet.is_type(SMSG_MAP_LOGIN_SUCCESS): # connected
                logger.info("Map login success.")
                packet.skip(4)
                coord_data = packet.read_coord_dir()
                coord_x = coord_data[0]
                coord_y = coord_data[1]
                coord_dir = coord_data[2]
                logger.info("Starting Postion: %s %s %s", coord_map, coord_x, coord_y)
                mapserv.sendall(str(PacketOut(CMSG_MAP_LOADED))) # map loaded
                # A Thread to send a shop broadcast: also keeps the network active to prevent timeouts.
                shop_broadcaster.start()

            elif packet.is_type(SMSG_WHISPER):
                msg_len = packet.read_int16() - 26
                nick = packet.read_string(24)
                message = packet.read_raw_string(msg_len)
                # Clean up the logs.
                if nick != 'AuctionBot':
                    logger.info("Whisper: " + nick + ": " + message)
                process_whisper(nick, utils.remove_colors(message), mapserv)

            elif packet.is_type(SMSG_PLAYER_STAT_UPDATE_1):
                stat_type = packet.read_int16()
                value = packet.read_int32()
                if stat_type == 0x0018:
                    logger.info("Weight changed from %s/%s to %s/%s", \
                    WEIGHT, MaxWEIGHT, value, MaxWEIGHT)
                    WEIGHT = value
                elif stat_type == 0x0019:
                    logger.info("Max Weight: %s", value)
                    MaxWEIGHT = value

            elif packet.is_type(SMSG_PLAYER_STAT_UPDATE_2):
                stat_type = packet.read_int16()
                value = packet.read_int32()
                if stat_type == 0x0014:
                    logger.info("Money Changed from %s, to %s", MONEY, value)
                    MONEY = value

            elif packet.is_type(SMSG_PLAYER_WARP):
                coord_map = packet.read_string(16)
                coord_.x = packet.read_int16()
                coord_y = packet.read_int16()
                logger.info("Player warped: %s %s %s", coord_map, coord_x, coord_y)
                mapserv.sendall(str(PacketOut(CMSG_MAP_LOADED)))

            elif packet.is_type(SMSG_TRADE_REQUEST):
                playername = packet.read_string(24)
                logger.info("Trade request: " + playername)
                mapserv.sendall(trade_respond(False))

            elif packet.is_type(SMSG_TRADE_RESPONSE):
                response = packet.read_int8()
                time.sleep(0.2)
                if response == 0:
                    logger.info("Trade response: Too far away.")
                    mapserv.sendall(whisper(playername, "You are too far away."))
                    trader_state.reset()

                elif response == 3:
                    logger.info("Trade response: Trade accepted.")
                    mapserv.sendall(str(PacketOut(CMSG_TRADE_ADD_COMPLETE)))

                else:
                    logger.info("Trade response: Trade cancelled")
                    trader_state.reset()

            elif packet.is_type(SMSG_TRADE_ITEM_ADD):
                mapserv.sendall(str(PacketOut(CMSG_TRADE_OK)))

            elif packet.is_type(SMSG_TRADE_ITEM_ADD_RESPONSE):
                packet.skip(4)
                response = packet.read_int8()

                if response == 0:
                    logger.info("Trade item add response: Successfully added item.")

                elif response == 1:
                    logger.info("Trade item add response: Failed - player overweight.")
                    mapserv.sendall(str(PacketOut(CMSG_TRADE_CANCEL_REQUEST)))
                    mapserv.sendall(whisper(playername, "You are carrying too much weight. Unload and try again."))
                elif response == 2:
                    mapserv.sendall(whisper(playername, "You have no free slots."))
                    logger.info("Trade item add response: Failed - No free slots.")
                    mapserv.sendall(str(PacketOut(CMSG_TRADE_CANCEL_REQUEST)))
                else:
                    logger.info("Trade item add response: Failed - unknown reason.")
                    mapserv.sendall(str(PacketOut(CMSG_TRADE_CANCEL_REQUEST)))
                    mapserv.sendall(whisper(playername, "Sorry, a problem has occured."))

            elif packet.is_type(SMSG_TRADE_OK):
                is_ok = packet.read_int8() # 0 is ok from self, and 1 is ok from other
                if is_ok == 0:
                    logger.info("Trade OK.")

            elif packet.is_type(SMSG_TRADE_CANCEL):
                trader_state.reset()
                logger.info("Trade Cancel.")

            elif packet.is_type(SMSG_TRADE_COMPLETE):
                trader_state.reset()
                logger.info("Trade Complete.")

            else:
                pass

    # On Disconnect/Exit
    logger.info("Server disconnect.")
    shop_broadcaster.stop()
    mapserv.close()

if __name__ == '__main__':
    main()
