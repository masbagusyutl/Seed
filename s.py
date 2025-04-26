import os
import time
import random
import json
import requests
import traceback
import re
import urllib.parse
from datetime import datetime, timedelta
import threading
from colorama import Fore, Style, init

# Inisialisasi colorama
init(autoreset=True)

def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop Seed")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop")

def extract_username(telegram_data):
    """Extract username from the telegram data"""
    try:
        # Decode URL-encoded data
        decoded_data = urllib.parse.unquote(telegram_data)
        
        # Try to find the username pattern
        username_match = re.search(r'"username"\s*:\s*"([^"]+)"', decoded_data)
        if username_match:
            return username_match.group(1)
            
        # If username not found, try to get first_name
        first_name_match = re.search(r'"first_name"\s*:\s*"([^"]+)"', decoded_data)
        if first_name_match:
            return first_name_match.group(1)
            
        # If both not found, try to get id
        id_match = re.search(r'"id"\s*:\s*(\d+)', decoded_data)
        if id_match:
            return f"ID_{id_match.group(1)}"
            
        return "Unknown"
    except Exception as e:
        return "Unknown"

def load_accounts():
    try:
        with open('data.txt', 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + "File data.txt tidak ditemukan!")
        return []

def load_proxies(filename='proxy.txt'):
    """Load proxies from a file, handling both authenticated and simple proxies"""
    try:
        with open(filename, 'r') as file:
            proxies = []
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(":")
                    if len(parts) == 4:
                        ip, port, user, password = parts
                        proxy_url = f"http://{user}:{password}@{ip}:{port}"
                    elif len(parts) == 2:
                        ip, port = parts
                        proxy_url = f"http://{ip}:{port}"
                    else:
                        continue
                    proxies.append(proxy_url)
        
        if proxies:
            print(Fore.BLUE + f"Berhasil memuat {len(proxies)} proxy.")
        return proxies
    except FileNotFoundError:
        print(Fore.YELLOW + f"File {filename} tidak ditemukan. Melanjutkan tanpa proxy.")
        return []

def get_proxy(proxies):
    """Retrieve a random proxy"""
    if not proxies:
        return None
    proxy_url = random.choice(proxies)
    return {"http": proxy_url, "https": proxy_url}

def format_line(text, color=Fore.WHITE):
    """Format line for better readability"""
    terminal_width = os.get_terminal_size().columns
    if len(text) > terminal_width:
        # Split text into multiple lines if too long
        lines = []
        current_line = ""
        for word in text.split():
            if len(current_line) + len(word) + 1 <= terminal_width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return color + "\n".join(lines)
    return color + text

def save_high_balance_accounts(username, balance):
    """Save accounts with high balance to a file"""
    GEM_THRESHOLD = 500  # Threshold for considering 'high balance'
    
    if balance >= GEM_THRESHOLD:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('high_balance_accounts.txt', 'a') as file:
            file.write(f"{timestamp} | {username} | {balance} gems\n")
        print(format_line(f"💎 Akun {username} memiliki {balance} gems! Disimpan ke high_balance_accounts.txt", Fore.MAGENTA))

def signin_telegram(account_data, proxies=None):
    """Sign in to telegram with the provided account data"""
    url = "https://alb.seeddao.org/api/v1/auth/sign-in/telegram"
    
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "alb.seeddao.org",
        "Origin": "https://cf.seeddao.org",
        "Referer": "https://cf.seeddao.org/",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    
    try:
        # Use the whole account_data as telegramData
        payload = {
            "telegram_data": account_data
        }
        
        proxy = get_proxy(proxies)
        response = requests.post(url, headers=headers, json=payload, proxies=proxy)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "token" in data["data"]:
                return data["data"]["token"], None
            else:
                return None, "Token tidak ditemukan dalam respons"
        else:
            return None, f"Gagal login: HTTP {response.status_code} - {response.text}"
    
    except Exception as e:
        return None, f"Error saat login: {str(e)}"

def get_account_info(token, proxies=None):
    """Get account information and available tasks"""
    info = {}
    
    # Headers for authenticated requests
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": f"Bearer {token}",
        "Connection": "keep-alive",
        "content-type": "application/json",
        "Host": "alb.seeddao.org",
        "Origin": "https://cf.seeddao.org",
        "Referer": "https://cf.seeddao.org/",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    
    try:
        # Get gems balance
        proxy = get_proxy(proxies)
        gems_response = requests.get(
            "https://alb.seeddao.org/api/v1/protected/gems/me",
            headers=headers,
            proxies=proxy
        )
        
        if gems_response.status_code == 200:
            gems_data = gems_response.json()
            if "data" in gems_data and "balance" in gems_data["data"]:
                info["balance"] = gems_data["data"]["balance"]
            else:
                info["balance"] = 0
        else:
            print(format_line(f"Gagal mendapatkan saldo: HTTP {gems_response.status_code}", Fore.RED))
            info["balance"] = 0
        
        # Get available tasks
        tasks_response = requests.get(
            "https://alb.seeddao.org/api/v1/protected/tasks/progresses",
            headers=headers,
            proxies=proxy
        )
        
        if tasks_response.status_code == 200:
            tasks_data = tasks_response.json()
            if "data" in tasks_data and "categories" in tasks_data["data"]:
                info["tasks"] = []
                
                # Extract tasks from the response
                for category in tasks_data["data"]["categories"]:
                    for group in category.get("groups", []):
                        for task in group.get("tasks", []):
                            info["tasks"].append({
                                "id": task["id"],
                                "name": task["name"],
                                "type": task["type"],
                                "reward": task["reward_amount"],
                                "repeats": task["repeats"]
                            })
            else:
                info["tasks"] = []
        else:
            print(format_line(f"Gagal mendapatkan tugas: HTTP {tasks_response.status_code}", Fore.RED))
            info["tasks"] = []
        
        return info
        
    except Exception as e:
        print(format_line(f"Error saat mengambil informasi akun: {str(e)}", Fore.RED))
        return {"balance": 0, "tasks": []}

def complete_task(token, task_id, proxies=None):
    """Complete a specific task"""
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": f"Bearer {token}",
        "Connection": "keep-alive",
        "content-type": "application/json",
        "Host": "alb.seeddao.org",
        "Origin": "https://cf.seeddao.org",
        "Referer": "https://cf.seeddao.org/",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    
    try:
        proxy = get_proxy(proxies)
        response = requests.post(
            f"https://alb.seeddao.org/api/v1/protected/tasks/{task_id}",
            headers=headers,
            proxies=proxy
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "notification_id" in data["data"]:
                notification_id = data["data"]["notification_id"]
                
                # Collect reward
                reward_response = requests.get(
                    f"https://alb.seeddao.org/api/v1/protected/tasks/notification/{notification_id}",
                    headers=headers,
                    proxies=proxy
                )
                
                if reward_response.status_code == 200:
                    reward_data = reward_response.json()
                    if ("data" in reward_data and 
                        "data" in reward_data["data"] and 
                        "completed" in reward_data["data"]["data"] and 
                        reward_data["data"]["data"]["completed"]):
                        
                        reward_amount = reward_data["data"]["data"]["reward_amount"]
                        return True, reward_amount
                    else:
                        return False, "Tugas belum selesai"
                else:
                    return False, f"Gagal mengambil hadiah: HTTP {reward_response.status_code}"
            else:
                return False, "ID notifikasi tidak ditemukan"
        else:
            return False, f"Gagal menyelesaikan tugas: HTTP {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Error saat menyelesaikan tugas: {str(e)}"

def process_account(account_data, account_index, total_accounts, proxies=None):
    """Process a single account"""
    print(format_line(f"\n{'='*50}", Fore.CYAN))
    
    # Extract username for display
    username = extract_username(account_data)
    
    print(format_line(f"Memproses akun {account_index + 1}/{total_accounts}: {username}", Fore.CYAN))
    
    try:
        # Login to telegram
        token, error = signin_telegram(account_data, proxies)
        
        if error:
            print(format_line(f"Gagal login: {error}", Fore.RED))
            return False
        
        print(format_line("Login berhasil!", Fore.GREEN))
        
        # Get account information
        account_info = get_account_info(token, proxies)
        
        balance = account_info['balance']
        print(format_line(f"Saldo gems: {balance}", Fore.BLUE))
        
        # Check if balance is 500 or more and save to file
        save_high_balance_accounts(username, balance)
        
        print(format_line(f"Tugas tersedia: {len(account_info['tasks'])}", Fore.BLUE))
        
        # Complete each task
        total_rewards = 0
        completed_tasks = 0
        
        for task in account_info["tasks"]:
            print(format_line(f"Mengerjakan tugas: {task['name']} (Reward: {task['reward']})", Fore.YELLOW))
            
            success, result = complete_task(token, task['id'], proxies)
            
            if success:
                completed_tasks += 1
                total_rewards += result
                print(format_line(f"✅ Berhasil! Mendapatkan {result} gems", Fore.GREEN))
            else:
                print(format_line(f"❌ Gagal: {result}", Fore.RED))
            
            # Short delay between tasks
            time.sleep(1)
        
        print(format_line(f"Selesai memproses akun. Tugas selesai: {completed_tasks}/{len(account_info['tasks'])}", Fore.GREEN))
        print(format_line(f"Total reward: {total_rewards} gems", Fore.GREEN))
        
        # Check final balance after tasks
        final_account_info = get_account_info(token, proxies)
        final_balance = final_account_info['balance']
        
        if final_balance != balance:
            print(format_line(f"Saldo gems baru: {final_balance} (Bertambah: {final_balance - balance})", Fore.BLUE))
            # Check again if balance reaches threshold after tasks
            save_high_balance_accounts(username, final_balance)
        
        return True
        
    except Exception as e:
        print(format_line(f"Error tidak terduga: {str(e)}", Fore.RED))
        traceback.print_exc()
        return False

def countdown_timer(duration_seconds):
    """Display a countdown timer"""
    end_time = datetime.now() + timedelta(seconds=duration_seconds)
    
    while datetime.now() < end_time:
        remaining = end_time - datetime.now()
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        countdown_str = f"\rMenunggu proses berikutnya: {hours:02d}:{minutes:02d}:{seconds:02d}"
        print(countdown_str, end='', flush=True)
        
        time.sleep(1)
    
    print("\nWaktu tunggu selesai! Memulai proses baru...")

def main():
    print_welcome_message()
    
    # Load accounts and proxies
    accounts = load_accounts()
    proxies = load_proxies()
    
    if not accounts:
        print(format_line("Tidak ada akun yang ditemukan di data.txt", Fore.RED))
        return
    
    print(format_line(f"Total akun dimuat: {len(accounts)}", Fore.GREEN))
    
    # Create high balance accounts file if it doesn't exist
    if not os.path.exists('high_balance_accounts.txt'):
        with open('high_balance_accounts.txt', 'w') as file:
            file.write("# Akun dengan saldo 500+ gems\n")
            file.write("# Format: Timestamp | Username | Saldo\n")
            file.write("="*50 + "\n")
    
    while True:
        # Process each account
        for i, account in enumerate(accounts):
            # Process the account
            success = process_account(account, i, len(accounts), proxies)
            
            # Add delay between accounts
            if i < len(accounts) - 1:
                print(format_line(f"\nMenunggu 5 detik sebelum memproses akun berikutnya...", Fore.YELLOW))
                time.sleep(5)
        
        print(format_line("\nSemua akun telah diproses. Menunggu 1 hari sebelum memulai ulang.", Fore.CYAN))
        
        # 1 day countdown timer (86400 seconds)
        countdown_timer(86400)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(format_line("\nProgram dihentikan oleh pengguna.", Fore.YELLOW))
    except Exception as e:
        print(format_line(f"\nError tidak terduga: {str(e)}", Fore.RED))
        traceback.print_exc()
