import socket
import sys

SERVER_HOST = '192.168.8.33'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"Mencoba terhubung ke server di {SERVER_HOST} : {SERVER_PORT}...")
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print("\nBerhasil terhubung. Ketik 'quit' atau 'exit' untuk keluar.")
    except socket.error as e:
        print(f"Gagal terhubung ke server: {e}")
        sys.exit()

    try:
        initial_message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        if initial_message:
            print(f"\n[SERVER] {initial_message.strip()}")

        while True:
            prompt = "\nNasgorBot >> "
            user_input = input(prompt)

            if user_input.lower() in ['quit', 'exit']:
                print("Menutup koneksi...")
                break
            
            client_socket.sendall(user_input.encode('utf-8'))
            
            server_response = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            
            if not server_response:
                print("Server menutup koneksi.")
                break
                
            print(f"[BOT] {server_response.strip()}")
            
    except KeyboardInterrupt:
        print("\n\nKlien dihentikan.")
    except Exception as e:
        print(f"Terjadi kesalahan komunikasi: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_client()