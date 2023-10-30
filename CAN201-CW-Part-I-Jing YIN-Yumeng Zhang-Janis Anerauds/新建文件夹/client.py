from socket import *
import time
import json
import struct
import hashlib
import argparse
import os
from os.path import getsize
import time


def _argparse():
    """Parses arguments from the CLI input
    """
    parse = argparse.ArgumentParser()
    parse.add_argument("-server_ip", default='', action='store', required=True, dest="server_ip",
                       help="The IP address of the server.")
    parse.add_argument("-id", default='', action='store', required=True, dest="id",
                       help="Cliet ID number")
    parse.add_argument("-f", default="", action="store", required=True, dest="file_path",
                       help="Path to the file to be sent to the server")
    return parse.parse_args()


def create_packet(json_data, bin_data=None):
    """Creates packet to send to the server, takes json_data and binary data
    """
    j = json.dumps(dict(json_data), ensure_ascii=False)
    j_len = len(j)
    if bin_data is None:
        return struct.pack('!II', j_len, 0) + j.encode()
    else:
        return struct.pack('!II', j_len, len(bin_data)) + j.encode() + bin_data


def get_tcp_packet(conn):
    """
    Receive a complete TCP "packet" from a TCP stream and get the json data and binary data.
    :param conn: the TCP connection
    :return:
        json_data
        bin_data
    """
    bin_data = b''
    while len(bin_data) < 8:
        data_rec = conn.recv(8)
        if data_rec == b'':
            time.sleep(0.01)
        if data_rec == b'':
            return None, None
        bin_data += data_rec
    data = bin_data[:8]
    bin_data = bin_data[8:]
    j_len, b_len = struct.unpack('!II', data)
    while len(bin_data) < j_len:
        data_rec = conn.recv(j_len)
        if data_rec == b'':
            time.sleep(0.01)
        if data_rec == b'':
            return None, None
        bin_data += data_rec
    j_bin = bin_data[:j_len]

    try:
        json_data = json.loads(j_bin.decode())
    except Exception as ex:
        return None, None

    bin_data = bin_data[j_len:]
    while len(bin_data) < b_len:
        data_rec = conn.recv(b_len)
        if data_rec == b'':
            time.sleep(0.01)
        if data_rec == b'':
            return None, None
        bin_data += data_rec
    return json_data, bin_data


def get_file_md5(filename):
    """
    Get MD5 value for big file
    :param filename:
    :return:
    """
    m = hashlib.md5()
    with open(filename, 'rb') as fid:
        while True:
            d = fid.read(2048)
            if not d:
                break
            m.update(d)
    return m.hexdigest()


def get_time_based_filename(ext, prefix='', t=None):
    """
    Get a filename based on time
    :param ext: ext name of the filename
    :param prefix: prefix of the filename
    :param t: the specified time if necessary, the default is the current time. Unix timestamp
    :return:
    """
    ext = ext.replace('.', '')
    if t is None:
        t = time.time()
    if t > 4102464500:
        t = t / 1000
    return time.strftime(f"{prefix}%Y%m%d%H%M%S." + ext, time.localtime(t))


def run(ip, id, file):
    """Main function to run the client, takes all the needed information to connecto the
    server and send the file, needs ip, id and file path all taken from arguments provided
    provided by argparse
    """
    serverName = ip
    serverPort = 1379
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    username = id
    login = {
        "type": "AUTH",
        "operation": "LOGIN",
        "direction": "REQUEST",
        "username": username,
        "password": hashlib.md5(username.encode()).hexdigest().lower()
    }
    clientSocket.send(create_packet(login))
    server_response_json, bin_data = get_tcp_packet(clientSocket)
    loginToken = server_response_json["token"]
    print("Token: " + server_response_json["token"])

    if os.path.exists(file) is False:
        print("File path does not exist, there has been an error")
        return

    path, key = os.path.split(file)
    file_size = getsize(file)
    upload_permission = {
        "type": "FILE",
        "operation": "SAVE",
        "direction": "REQUEST",
        "token": loginToken,
        "size": file_size,
        "key": key
    }
    clientSocket.send(create_packet(upload_permission))
    server_response_json, bin_data = get_tcp_packet(clientSocket)

    if server_response_json["status"] == 402:
        key = get_time_based_filename("-").replace(".", "") + key
        upload_permission = {
            "type": "FILE",
            "operation": "SAVE",
            "direction": "REQUEST",
            "token": loginToken,
            "size": file_size,
            "key": key
        }
        clientSocket.send(create_packet(upload_permission))
        server_response_json, bin_data = get_tcp_packet(clientSocket)

    file_key = server_response_json["key"]
    total_blocks = server_response_json["total_block"]
    block_size = server_response_json["block_size"]
    file_md5 = get_file_md5(file)

    start_time = time.time()
    with open(file, "rb") as fid:
        block_index = 0
        while block_index != total_blocks:
            fid.seek(block_size * block_index)
            if block_size * (block_index + 1) < file_size:
                bin_data = fid.read(block_size)
            else:
                bin_data = fid.read(file_size - block_size * block_index)

            upload_file = {
                "type": "FILE",
                "operation": "UPLOAD",
                "direction": "REQUEST",
                "token": loginToken,
                "key": file_key,
                "block_index": block_index,
            }
            clientSocket.send(create_packet(upload_file, bin_data))
            server_response_json, bin_data = get_tcp_packet(clientSocket)
            print(server_response_json)

            block_index += 1
    if server_response_json["md5"] == file_md5:
        print("Server has received file properly, md5 match! MD5: " + file_md5)
    else:
        print("Error file has been wrongfully uploaded md5 do not match")
    clientSocket.close()


if __name__ == "__main__":
    """takes arguments from argparse and runs the run function with arguments present
    """
    start_time = time.time()
    parser = _argparse()
    server_ip = parser.server_ip
    student_id = parser.id