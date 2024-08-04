import os
from server_handler import ServerHandler
from servers import Servers
import re


def add_server() -> None:
    label = input("Enter server label: ")
    username = input("Enter server username: ")
    ip = input("Enter server ip: ")
    if re.match(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$", ip) is None:
        return print("Invalid ip")
    try:
        port = get_port("Enter server port: ")
    except AssertionError:
        return print("Invalid port")
    ports = get_ports()
    servers.servers.append(ServerHandler(ip, port, username, ports, label))

def get_ports() -> list:
    ports = []
    print("Enter knock ports one by one. Enter q to finish")
    try:
        while True:
            ports.append(get_port("Enter knock port: "))
    except AssertionError: return ports

def get_port(msg: str = "Enter port: ") -> int:
    while True:
        try:
            port = input(msg)
            assert port != "q"
            port = int(port)
            if port > 65535 or port < 1: 
                print("Invalid port")
                continue
            return port
        except ValueError: print("Invalid port")

def choose_menu() -> None:
    while True:
        os.system("cls")
        print("Servers:")
        for i, server in enumerate(servers.servers):
            print(f"{i + 1}.", server)
        back = len(servers.servers) + 1
        print(f"{back}. Back")
        choice = input("Choose an option: ")
        choice = int(choice)
        if choice <= 0 or choice > back: 
            print("Invalid option")
            continue
        if choice == back: break
        server_menu(servers.servers[choice - 1])

def server_menu(server: ServerHandler) -> None:
    answer = ""
    while True:
        os.system("cls")
        print(answer, end="\n" if answer else "")
        print(server)
        print("1. Connect server")
        print("2. Knock server")
        print("3. Reboot server")
        print("4. Get SSH keys") 
        print("5. Set up server (initialize port knocking)") 
        print("6. Link port")
        print("7. Server settings")
        print("8. Back")
        _choice = input("Choose an option: ")
        answer = ""
        match _choice:
            case "1": server.connect_server()
            case "2": server.knock_server()
            case "3": server.reboot()
            case "4": answer = server.get_ssh_key()
            case "5": server.init_server()
            case "6": server.link_port(get_port())
            case "7": 
                if settings_menu(server): break
            case "8": break
            case _: print("Invalid option")

def settings_menu(server: ServerHandler) -> bool:
    while True:
        os.system("cls")
        print(server)
        print("1. Set server port")
        print("2. Set knock ports")
        print("3. Delete server")
        print("4. Back")
        choice = input("Choose an option: ")
        match choice:
            case "1": server.set_port(get_port())
            case "2": server.set_knock_ports(get_ports())
            case "3":
                server.die()
                servers.servers.remove(server)
                return True
            case "4": break
            case _: print("Invalid option")
    return False

def main_menu() -> None:
    while True:
        os.system("cls")
        print("Servers manager")
        print("1. Choose server")
        print("2. Add server")
        print("3. Exit")
        choice = input("Choose an option: ")
        match choice:
            case "1": choose_menu()
            case "2": add_server()
            case "3": break
            case _: print("Invalid option")

if __name__ == "__main__":
    servers = Servers()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("Exiting...\n")
