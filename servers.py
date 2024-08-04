from pathlib import Path
from typing import Any, Generator
from server_handler import ServerHandler

class Servers:
    def __init__(self) -> None:
        self.script_paths = {
            'init_path': Path(f"scripts/init/"),
            'knock_path': Path(f"scripts/knock/"),
            'connect_path': Path(f"scripts/connect/")
        }
        self.servers = list(self.get_servers())

    def get_servers(self) -> Generator[ServerHandler, Any, Any]:
        data = {}
        for path in self.script_paths.get('connect_path').iterdir():
            server = {
                "ip": "",
                "port": 0,
                "username": "",
                "ports": [],
                "label": path.name.split(".")[0],
            }
            server.update(self.get_server(path))
            server.update(self.get_ports(self.script_paths.get('knock_path') / path.name))
            data.update({path.stem: server})
        for server in data.values():
            yield ServerHandler(
                server.get("ip"), 
                server.get("port"), 
                server.get("username"), 
                server.get("ports"),
                server.get("label"),
            )
        
    def get_server(self, path: Path) -> dict:
        data = {}
        with open(path, "r") as f:
            command = f.readline().split(" ")
            data["ip"] = command[1].split("@")[1]
            data["username"] = command[1].split("@")[0]
            data["port"] = int(command[-1])
        return data

    def get_ports(self, path: Path) -> dict:
        data = {"ports": []}
        with open(path, 'r') as f:
            for line in f.readlines():
                data.get("ports").append(line.split(" ")[-2])
        return data