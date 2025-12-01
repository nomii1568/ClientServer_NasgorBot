import socket
import select
import sys
import json
import os
from difflib import SequenceMatcher

# --- Konfigurasi Server
# HOST = '0.0.0.0'
HOST = '192.168.8.33'
PORT = 12345
BUFFER_SIZE = 1024
FAQ_FILE = 'faq_data.json'

FAQ_DATA = []
MIN_WORD_MATCH_RATIO = 0.70
MIN_KEYWORD_OVERLAP = 1 

def load_faq_data():
    global FAQ_DATA
    try:
        with open(FAQ_FILE, 'r', encoding='utf-8') as f:
            FAQ_DATA = json.load(f)
        print(f"Database FAQ berhasil dimuat ({len(FAQ_DATA)} entries).")
        return True
    except FileNotFoundError:
        print(f"ERROR: File FAQ tidak ditemukan.")
        return False
    except json.JSONDecodeError as e:
        print(f"ERROR: Kesalahan format JSON dalam '{FAQ_FILE}': {e}")
        return False
    
def get_best_match(query_str):
    query_tokens = query_str.split()
    
    best_overlap_count = 0
    best_answer = None
    best_matched_keywords = ""
    
    for entry in FAQ_DATA:
        current_overlap_count = 0
        keyword_total = len(entry['keywords'])
        matched_keywords = []
        
        for faq_keyword in entry['keywords']:
            for query_token in query_tokens:
                
                score = SequenceMatcher(None, query_token, faq_keyword).ratio()
                
                if score >= MIN_WORD_MATCH_RATIO:
                    current_overlap_count += 1
                    matched_keywords.append(faq_keyword)
                    break 
        
        if current_overlap_count > best_overlap_count:
            best_overlap_count = current_overlap_count
            best_answer = entry['answer']
            best_matched_keywords = ", ".join(set(matched_keywords))
            best_keyword_total = keyword_total
            
    if best_overlap_count >= MIN_KEYWORD_OVERLAP:
        if best_keyword_total > 0:
            overlap_percentage = int((best_overlap_count / best_keyword_total) * 100)
        else:
            overlap_percentage = 100
        
        correction_message = f"(Ditemukan kecocokan {overlap_percentage}% dengan kata kunci: '{best_matched_keywords}')\n"
        return (correction_message + best_answer).encode('utf-8')
    
    else:
        return "Maaf, pertanyaan Anda tidak dimengerti oleh bot dan bot tidak menemukan topik yang sesuai. Coba tanyakan topik seputar Nasi Goreng.".encode('utf-8')

def process_query(data):
    query_str = data.decode('utf-8').strip().lower()
    
    if not query_str:
        return "Mohon kirimkan pertanyaan Anda.".encode('utf-8')

    return get_best_match(query_str)

def start_server():
    if not load_faq_data():
        sys.exit(1)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    
    try:
        server_socket.bind((HOST, PORT))
        print(f"Server berhasil di-bind ke {HOST} : {PORT}")
    except Exception as e:
        print(f"Gagal melakukan Bind ke {HOST} : {PORT} : {e}")
        sys.exit()

    server_socket.listen(5)
    
    sockets_list = [server_socket]
    clients = {}

    while True:
        read_sockets, _, exceptional_sockets = select.select(sockets_list, [], sockets_list)
        
        for sock in read_sockets:
            if sock == server_socket:
                client_socket, client_address = server_socket.accept()
                
                sockets_list.append(client_socket)
                clients[client_socket] = client_address
                
                print(f"\nKoneksi baru diterima dari {client_address[0]} : {client_address[1]}\n")
                welcome_message = "Selamat datang di Auto-Resep Nasgor!\n".encode('utf-8')
                client_socket.send(welcome_message)

            else:
                try:
                    data = sock.recv(BUFFER_SIZE)

                    if not data:
                        address = clients.pop(sock)
                        sockets_list.remove(sock)
                        sock.close()
                        print(f"Koneksi ditutup oleh klien: {address[0]} : {address[1]}")
                        continue

                    address = clients[sock]
                    print(f"Pesan dari {address[0]} : {address[1]} -> {data.decode('utf-8').strip()}")
                    
                    response = process_query(data)
                    
                    response_to_send = response + b'\n'
                    sock.send(response_to_send)
                    print(f"Balasan dikirim ke {address[0]} : {address[1]}\n")
                        
                except Exception as e:
                    if sock in clients:
                        address = clients.pop(sock)
                        print(f"Error saat menerima data dari {address[0]} : {address[1]}: {e}. Menutup koneksi.\n")
                    
                    if sock in sockets_list:
                        sockets_list.remove(sock)
                    sock.close()

        for sock in exceptional_sockets:
            if sock in clients:
                address = clients.pop(sock)
                print(f"Pengecualian pada soket: {address[0]} : {address[1]}. Menutup koneksi.\n")
            if sock in sockets_list:
                sockets_list.remove(sock)
            sock.close()


if __name__ == "__main__":
    start_server()