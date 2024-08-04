import os
from pathlib import Path
import subprocess


class ServerHandler:
    def __init__(self, ip: str, port: int, username: str, ports: list[int] = [1337, 2938, 2342], label: str = "server") -> None:
        self.ip = ip
        self.port = port
        self.username = username
        self.ports = ports
        self.label = label
        self.script_paths: dict[str, Path] = {
            'init_path': Path(f"scripts/init/{self.label}.{self.ip}.{self.port}.sh"),
            'knock_path': Path(f"scripts/knock//{self.label}.{self.ip}.{self.port}.bat"),
            'connect_path': Path(f"scripts/connect//{self.label}.{self.ip}.{self.port}.bat"),
            'key_path': Path(f"keys//{self.label}.{self.ip}.{self.port}.pub")
        }
        
        self.initialized = False
        self.check_key()
        
        if not self.script_paths.get('connect_path').exists():
            self.write_scripts()

    def set_port(self, new_port: int) -> None:
        self.port = new_port
    
    def set_knock_ports(self, new_ports: list[int]) -> None:
        self.ports = new_ports
    
    def get_init_script(self) -> str:
        return f"""#!/bin/bash
# ---------------------------------------------------------
# Dont forget to turn off Safety Groups at vps provider web
# interface settings every time you create new vps instance.
# ---------------------------------------------------------
# To check iptables use
# sudo iptables -L --line-numbers
# ---------------------------------------------------------
adapter=$(ip -o -4 route show to default | awk '{{print $5}}')
port={self.port}

sudo apt update
sudo apt upgrade -y
echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | sudo debconf-set-selections
sudo apt install -y python-is-python3 knockd tmux zsh mc vim git iptables-persistent
sudo apt autoremove -y


echo "Port $port
PermitRootLogin no
PasswordAuthentication no
AllowUsers vegameta" | sudo tee -a /etc/ssh/sshd_config

echo "
127.0.1.1   $(hostname)
" | sudo tee -a /etc/hosts

echo "[options]
    UseSyslog
    Interface 		= $adapter

[SSH]
    sequence        = {",".join(map(str, self.ports))}
    seq_timeout     = 9
    tcpflags        = syn
    start_command   = /sbin/iptables -I INPUT -s %IP% -p tcp --dport $port -j ACCEPT
    stop_command    = /sbin/iptables -D INPUT -s %IP% -p tcp --dport $port -j ACCEPT
    cmd_timeout     = 25" | sudo tee /etc/knockd.conf

echo "START_KNOCKD=1
KNOCKD_OPTS=\"-i $adapter\"" | sudo tee /etc/default/knockd

sudo service ssh restart
sudo systemctl start knockd
sudo systemctl enable knockd
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -p tcp --dport $port -j REJECT
sudo iptables -A INPUT -p icmp --icmp-type 8 -j DROP
sudo service netfilter-persistent save
sudo /etc/init.d/networking restart


echo "auth      sufficient      pam_shells.so
auth      sufficient      pam_rootok.so
@include common-auth
@include common-account
@include common-session" | sudo tee /etc/pam.d/chsh > /dev/null

echo "set-option -g default-shell /bin/zsh" | sudo tee ~/.tmux.conf

chsh -s /usr/bin/tmux

sh -c "$(wget https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)" "" --unattended

ssh-keygen -t ed25519 -q -N "" -f ~/.ssh/id_ed25519
clear
cat ~/.ssh/id_ed25519.pub""".replace('\r\n','\n')

    def die(self) -> None:
        for path in self.script_paths.values():
            os.remove(path)
    
    def get_knock_script(self) -> str:
        return "\n".join([f"nmap -Pn --max-retries 0 -p {port} {self.ip}" for port in self.ports])

    def get_connect_script(self) -> str:
        return f"ssh {self.username}@{self.ip} -p {self.port}"
    
    def write_script(self, path, script: str) -> None:
        open(path, 'w', newline='\n' if path.suffix == '.sh' else None).write(script)
    
    def transfer_init_script(self) -> None:
        subprocess.run(f"scp {self.script_paths.get('init_path')} {self.username}@{self.ip}:/home/{self.username}/init.sh")
    
    def knock_server(self) -> None:
        subprocess.run(str(self.script_paths.get('knock_path').absolute()))
        print("Server knocked")
    
    def connect_server(self) -> None:
        self.knock_server()
        subprocess.run("wt " + str(self.script_paths.get('connect_path').absolute()))

    def init_server(self) -> None:
        if not self.initialized:
            self.transfer_init_script()
            subprocess.run(f"ssh {self.username}@{self.ip} -t 'chmod +x ./init.sh; ./init.sh'")

    def get_ssh_key(self) -> None:
        if self.script_paths.get('key_path').exists():
            with open(self.script_paths.get('key_path'), 'r') as f:
                key = f.read()
                subprocess.Popen(['clip'], stdin=subprocess.PIPE).communicate(key.encode())
                return "SSH key copied to clipboard!\n"
        else:
            self.knock_server()
            subprocess.run(f"scp -P {self.port} {self.username}@{self.ip}:/home/{self.username}/.ssh/id_ed25519.pub {str(self.script_paths.get('key_path').absolute())}")
            self.check_key()
            if self.initialized: return "SSH key downloaded"
            else: return "Error occurred"

    def check_key(self) -> None:
        self.initialized = self.script_paths.get('key_path').exists()

    def write_scripts(self) -> None:
        self.write_script(self.script_paths.get('init_path'), self.get_init_script())
        self.write_script(self.script_paths.get('knock_path'), self.get_knock_script())
        self.write_script(self.script_paths.get('connect_path'), self.get_connect_script())
    
    def link_port(self, port: int) -> None:
        self.knock_server()
        try:
            subprocess.run(f"ssh -f -N -L {port}:localhost:{port} {self.username}@{self.ip} -p {self.port}", timeout=5)
        except subprocess.TimeoutExpired:
            print("Link request was sent")
    
    def reboot(self) -> None:
        self.knock_server()
        subprocess.run(f"ssh {self.username}@{self.ip} -p {self.port} -t 'sudo shutdown -r now'")
    
    def __repr__(self) -> str:
        return f"{self.label} {self.username}@{self.ip}:{self.port} knock ports {', '.join(map(str, self.ports))}"
