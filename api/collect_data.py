import re
import urllib.parse
from ast import literal_eval as make_tuple

import requests
from bs4 import BeautifulSoup

from .models import student


def read_data(xml):
    soup = BeautifulSoup(xml, "lxml")
    return soup


def get_pending_term(terms):
    latest = 0
    for index, term in enumerate(terms):
        if term["f4455"] == "مشغول به تحصيل _ عادي":
            latest = index
    if latest == 0:
        latest = index
    return latest


def get_grade_faculty_major(response):
    soup = BeautifulSoup(response.content, "html.parser")
    script = soup.find_all("script")[0].string
    faculty = re.findall("F61151 = \\'(.*?)\\';", script)[0]
    major = re.findall("F17551 = \\'(.*?)\\';", script)[0]
    grade = re.findall("F41301 = \\'(.*?)\\';", script)[0]
    grade_type = re.findall("F41351 = \\'(.*?)\\';", script)[0]

    return faculty, major, grade + "-" + grade_type


def get_grades(courses):
    ar = []
    for course in courses:
        courses_json = {
            "name": course["f0200"].strip(),
            "nomre": course["f3945"].strip(),
            "type": course["f3952"].strip(),
            "vahed": course["f0205"].strip(),
        }
        ar.append(courses_json)

    return ar


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def current_term_gpa(courses):
    summation = 0
    vahed = 0
    for course in courses:
        if is_float(course["nomre"]):
            summation += float(course["nomre"]) * float(course["vahed"])
            vahed += float(course["vahed"])
    if vahed == 0:
        return ""
    return str(
        round(
            summation / vahed,
            2,
        )
    )


def get_user_grades(user_info, s, session, response, u, lt, Stun):
    last_term = user_info["summery"]["termYear"]
    cookies = {
        "u": u,
        "lt": lt,
        "su": "3",
        "ft": "0",
        "f": "12310",
        "seq": str(get_seq(response)),
        "ASP.NET_SessionId": session,
        "sno": Stun,
        "stdno": Stun,
    }

    headers = {
        "Host": "golestan.ikiu.ac.ir",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "595",
        "Origin": "https://golestan.ikiu.ac.ir",
        "Dnt": "1",
        "Referer": "https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON"
        "/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx?r=0.41827066214011355&fid=0%3b12310&b=10&l=1&tck"
        "=9D871E0D-BE1C-4E&&lastm=20180201081222",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "frame",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Te": "trailers",
    }

    for index, term in enumerate(user_info["summery"]["Allterms"]):
        ctck = get_ticket(response)
        params = (
            ("r", "0.41827066214011355"),
            ("fid", "0;12310"),
            ("b", "10"),
            ("l", "1"),
            ("tck", ctck),
            ("lastm", "20180201081222"),
        )

        data = (
            f"__VIEWSTATE=PSqS0taw2jaS4YTMUVe78LFSqRY0nc2wknK4DQuC%2F9KPJNv4%2BKLkm5Gg489PZPW6o7JM%2FuKFXvX"
            f"%2FVkuDuHLyCQ3nwsDYNPfhBiuc6CCPBqpRQqP7Z6pQKhZMCTsq2IMTj09PgNxg6uFsUnIaaMpBxw%3D%3D"
            f"&__VIEWSTATEGENERATOR=6AC8DB9B&__EVENTVALIDATION=Vs8M%2B9nHFU621jB1fDojqspw9XtULz4rCjkLOBl3%2B4"
            f"%2B6w3KFDV%2BVcv3O%2F8YEONVav%2F%2BX%2BlVcW7L9KzYgQRRQakCNziokDrPK8ykb9cSPYl"
            f"%2B1cMX8DrpUGu0EUQQUDXMsgr26ETIbuaj9nzFDI6FS"
            f"%2B7xxsrW0OjSreXoTNbuZZ9aeURNKddDbnkicqURFZq42ZrL94C2I9yuXtRYky2gdu%2BV3F0HMCAnk"
            f"%2FTvvddr5YrIoHyTmUhpJmxBNi%2BimnjXlrlcMDNBBTGFCzohQQksOTA%3D%3D&Fm_Action=80&Frm_Type=0&Frm_No"
            f"=&TicketTextBox={ctck}&XMLStdHlp=&TxtMiddle=%3Cr+F41251%3D%22{Stun}%22+F43501%3D%22{term}%22%2F%3E&ex="
        )

        response = s.post(
            "https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx",
            headers=headers,
            params=params,
            cookies=cookies,
            data=data,
        )

        res = re.findall("T01XML='(.*)';", response.content.decode("utf-8"))[0]
        soup = read_data(res)
        courses = soup.find_all("n")[3:]
        course_data = get_grades(courses)
        if term == last_term:
            last_term_gpa = user_info["summery"]["data"][index]["moaddel"]
            if not last_term_gpa:
                user_info["summery"]["data"][index]["moaddel"] = current_term_gpa(course_data)

        user_info[term] = course_data

    return user_info


def get_user_info(terms, latest_term, Stun, faculty, major, grade):
    global Name
    term = terms[latest_term]
    user_info = {}
    user_data = {}
    ar = []
    for t in terms:
        temp = {"term": t["f4350"].strip(), "moaddel": t["f4360"].strip(), "vahed": t["f4365"].strip()}
        ar.append(temp)

    user_data["data"] = ar
    user_data["Allterms"] = [t["f4350"].strip() for index, t in enumerate(terms) if index <= latest_term]
    user_data["Voroodi"] = "1" + user_data["Allterms"][0][:-1]
    user_data["term"] = term["f4350"].strip()
    user_data["termYear"] = term["f4350"].strip()
    user_data["akhzShode"] = term["cumget"].strip()
    user_data["passShode"] = term["cumpas"].strip()
    user_data["moaddelKol"] = term["cumgpa"].strip()
    user_data["name"] = Name[0] + " " + Name[1]
    user_data["stun"] = Stun.strip()
    user_data["faculty"] = faculty.strip()
    user_data["major"] = major.strip()
    user_data["grade"] = grade.strip()
    user_info["summery"] = user_data
    return user_info


def get_ticket(response):
    soup = BeautifulSoup(response.content, "html.parser")
    ctck = soup.find_all("input", attrs={"id": "TicketTextBox"})[0].attrs["value"]
    return ctck


def get_user_name(response):
    soup = BeautifulSoup(response.content, "html.parser")
    name = soup.find_all("input", attrs={"name": "TxtMiddle"})[0].attrs["value"]
    name = re.search(r'<F80501 val="(.*)" /><F80551 val="(.*)" /><F83171', name)
    return name.group(1), name.group(2)


def get_seq(response):
    res = make_tuple(re.findall("parent.Commander.SavAut(.*?);", response.content.decode("utf-8"))[0])
    return res[6]


def get_session_id(response):
    return response.cookies.get_dict()["ASP.NET_SessionId"]


def login(stun, password):
    global Name
    login_url = "https://golestan.ikiu.ac.ir/Forms/AuthenticateUser/AuthUser.aspx"

    try:
        user = student.objects.get(stun=stun)
    except:
        user = student(stun=stun)

    json_response = {}
    captcha = ""
    password = urllib.parse.quote_plus(password)

    cookies = {
        "u": "",
        "lt": "",
        "su": "",
        "ft": "",
        "f": "",
        "seq": "",
    }

    headers = {
        "Host": "golestan.ikiu.ac.ir",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "585",
        "Origin": "https://golestan.ikiu.ac.ir",
        "Dnt": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "frame",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Te": "trailers",
    }

    data = (
        f"__VIEWSTATE"
        f"=%2FwEPDwUKMjA2NTYzNTQ5MmRk3pMVc3vrMpmJPeFlNuTZNAqnZ1IuvBAh7F6ibaOvjLcRmUq1Bo93homnh5DYRQi8BRW5Rzfi"
        f"%2BYZuKAERQqxuQQ%3D%3D&__VIEWSTATEGENERATOR=6A475423&__EVENTVALIDATION=%2FwEdAAZLlyHuYR3BLALr37"
        f"%2Bc2m3n4ALG8S7ZiLlJqSsuXBsjGz"
        f"%2FLlbfviBrHuco87ksZgLcCRt9NnSPADSFObzNVq3ShPZSQos3ErAwfDmhlNwH4qEsT6FfmV7ULQ7j"
        f"%2FFGM5sO5GzNDLxCLDFj1724Jc3Y%2BlrbM5jHMQ3800JLSzB8cvT0PujcljIJ7JpjSJMqHuPBKXt1c%2B%2BVTuIBSvjVJnUw2o"
        f"&TxtMiddle=%3Cr+F51851%3D%22%22+F80401%3D%22{password}%22+F80351%3D%22{stun}%22+F51701%3D%22"
        f"{captcha}%22+F83181%3D%22%22%2F%3E&Fm_Action=09&Frm_Type=&Frm_No=&TicketTextBox="
    )

    ## First request
    s = requests.Session()
    response = s.post(login_url, headers=headers, data=data, cookies=cookies)

    print("*" * 50, "First request:", "*" * 50)
    print(response.text)

    try:
        ctck = get_ticket(response)
    except:
        json_response["status"] = "نام کاربری/رمز عبور اشتباه است!"
        return json_response

    Name = get_user_name(response)
    full_name = Name[0] + " " + Name[1]
    user.name = full_name

    res_cookies = response.cookies.get_dict()

    print("*" * 50, "resCookie", "*" * 50)
    print(res_cookies)

    try:
        session = get_session_id(response)
    except:
        json_response["status"] = "بعلت لاگین بیش از حد توسط گلستان محدود شده اید. 1 ساعت دیگر دوباره وارد شوید."
        return json_response

    cookies = {
        "u": res_cookies["u"],
        "lt": res_cookies["lt"],
        "su": "0",
        "ft": "0",
        "f": "1",
        "ASP.NET_SessionId": session,
        "seq": str(get_seq(response)),
    }

    params = (
        ("r", "0.656196360363224"),
        ("fid", "0;11130"),
        ("b", ""),
        ("l", ""),
        ("tck", ctck),
        ("lastm", "20090829065642"),
    )

    ## Second request
    response = s.get(
        "https://golestan.ikiu.ac.ir/Forms/F0213_PROCESS_SYSMENU/F0213_01_PROCESS_SYSMENU_Dat.aspx",
        params=params,
        cookies=cookies,
    )

    print("*" * 50, "Second request", "*" * 50)
    print(response.text)

    print("*" * 50, "cookie", "*" * 50)
    print(cookies)

    print("*" * 50, "params", "*" * 50)
    print(params)

    try:
        ctck = get_ticket(response)
    except:
        json_response["status"] = "بعلت لاگین بیش از حد توسط گلستان محدود شده اید. 1 ساعت دیگر دوباره وارد شوید."
        return json_response

    res_cookies = response.cookies.get_dict()
    cookies = {
        "u": res_cookies["u"],
        "lt": res_cookies["lt"],
        "su": "3",
        "ft": "0",
        "f": "11130",
        "seq": str(get_seq(response)),
        "ASP.NET_SessionId": session,
        "ctck": ctck,
    }

    data = f"__VIEWSTATE=8PMg%2FXGkz21Jo6lFl1wV%2BG6zGMZJ27V9hN%2F" \
           f"%2FQtcDNf4oZUW5mb0b7v4bV56pVIyLXFbCuSPD3cvVNuY6kqj4z" \
           f"%2Bl8jWRZ5kGZgYaguBv4T27af0K1U3ZQwojfUXITMiBFjS1klAGeRDe2fRVcBFB3VA%3D%3D&__VIEWSTATEGENERATOR=25DF661B" \
           f"&__EVENTVALIDATION=LbkdlrW%2FdjGKFMfWRDzI72UlPjqWROfiKJOUDUusM%2FxEcdNdKbRSY2iWnir" \
           f"%2BZS2q14Ebo1ZEcVK0EoFGiRe7GYbblq13ynWnKvNE2FriZLj%2FCRnfLB%2BGykh" \
           f"%2BpJCvpq9UUsSqIntjbwDRsiQEPeQQ3dbfmIAZCNPeytCcgtqATCPXTdD3i4FXL7yjPixv82eAbJcxcUY0hKwjdHSRKmDESzVK" \
           f"%2FYQD2%2FFSW2qLX%2BytNTEZ57I%2BXBOAAr9QVJVuIw9u3KK27r%2FbycWoIN1m9zlSUA%3D%3D&Fm_Action=00&Frm_Type" \
           f"=&Frm_No=&TicketTextBox={ctck}&XMLStdHlp=&TxtMiddle=%3Cr%2F%3E&ex="

    headers1 = {
        "Host": "golestan.ikiu.ac.ir",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "2551",
        "Origin": "https://golestan.ikiu.ac.ir",
        "Dnt": "1",
        "Referer": "https://golestan.ikiu.ac.ir/Forms/F0202_PROCESS_REP_FILTER/F0202_01_PROCESS_REP_FILTER_DAT.ASPX?r"
        "=0.75486758742996&fid=1%3b102&b=10&l=1&tck=9691AB60-96A2-43&&lastm=20190829142532",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "frame",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Te": "trailers",
    }

    ## Third request - second request post
    response = s.post(
        "https://golestan.ikiu.ac.ir/Forms/F0213_PROCESS_SYSMENU/F0213_01_PROCESS_SYSMENU_Dat.aspx",
        params=params,
        cookies=cookies,
        data=data,
        headers=headers1,
    )

    print("*" * 50, "Third request - second request post", "*" * 50)
    print(response.text)

    print("*" * 50, "resCookie", "*" * 50)
    print(res_cookies)

    print("*" * 50, "cookie", "*" * 50)
    print(cookies)

    print("*" * 50, "params", "*" * 50)
    print(params)

    ctck = get_ticket(response)
    save_tick = ctck
    res_cookies = response.cookies.get_dict()
    cookies = {
        "u": res_cookies["u"],
        "lt": res_cookies["lt"],
        "su": "3",
        "ft": "0",
        "f": "11130",
        "seq": str(get_seq(response)),
        "ASP.NET_SessionId": session,
    }

    params = (
        ("r", "0.8500803687206074"),
        ("fid", "0;12310"),
        ("b", "10"),
        ("l", "1"),
        ("tck", ctck),
        ("lastm", "20190829142532"),
    )

    headers = {
        "Host": "golestan.ikiu.ac.ir",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://golestan.ikiu.ac.ir/_Templates/Commander.htm",
        "Dnt": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "frame",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Te": "trailers",
    }

    ## Fourth request
    response = s.get(
        "https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx",
        headers=headers,
        params=params,
        cookies=cookies,
    )

    print("*" * 50, "Fourth request", "*" * 50)
    print(response.text)

    print("*" * 50, "resCookie", "*" * 50)
    print(res_cookies)

    print("*" * 50, "cookie", "*" * 50)
    print(cookies)

    print("*" * 50, "params", "*" * 50)
    print(params)

    cookies = {
        "u": res_cookies["u"],
        "lt": res_cookies["lt"],
        "su": "3",
        "ft": "0",
        "f": "12310",
        "seq": str(get_seq(response)),
        "ASP.NET_SessionId": session,
        "stdno": "",
        "sno": "",
    }

    headers = {
        "Host": "golestan.ikiu.ac.ir",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "549",
        "Origin": "https://golestan.ikiu.ac.ir",
        "Dnt": "1",
        "Referer": "https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON"
        "/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx?r=0.08286821317886972&fid=0;12310&b=10&l=1&tck"
        "=6123BBB3-7555-49&&lastm=20180201081222",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "frame",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Te": "trailers",
    }

    ctck = get_ticket(response)
    params = (
        ("r", "0.8500803687206074"),
        ("fid", "0;12310"),
        ("b", "10"),
        ("l", "1"),
        ("tck", save_tick),
        ("lastm", "20230514110830"),
    )
    data = (
        f"__VIEWSTATE=%2B4JaHQdzFS0AQBA3xD5k4JLGZuFB2TvLEMSoO00eytx83bhToohV%2BGSK11jXdQ%2Bu%2BKMVMTjEO"
        f"%2BeM8774ddKWRIB5itd5khSxV25sBMwUpb%2B5M%2FmK%2BulXmM6qCxSfNnqtXrR%2BM51Vf71DDyJH3e5tIg%3D%3D"
        f"&__VIEWSTATEGENERATOR=6AC8DB9B&__EVENTVALIDATION=FGuN%2BlEw%2BVnPsZEf%2B"
        f"%2FUj0cwUzIZHUHxXaiNu04XCxH7myMpYXQUtUHEpELGv14hyq4wMzunzlrqlja7MrWZ5kBDBTLpfDMqW7LnqwNmtTWdGQOUeVUe33xiTE1%2FgOOPTzNYZeMaEkV9mz1TPW9Rr8PFcGPTFfTh4WRx1LqkYWllWTAxRal3vQGGp4QsqN1gCrG8trbSPBNzGLSvvxrIUMZelNEy3s7UxyydH5wouLoPTGSOZq6XSL1aKh%2BkL6cZEoxaCvyVHwoA5%2FtHBQm5G7A%3D%3D&Fm_Action=00&Frm_Type=&Frm_No=&TicketTextBox={ctck}&XMLStdHlp=&TxtMiddle=%3Cr%2F%3E&ex="
    )

    ## Fifth request
    response = s.post(
        "https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx",
        headers=headers,
        params=params,
        cookies=cookies,
        data=data,
    )

    print("*" * 50, "Fifth request", "*" * 50)
    print(response.text)

    print("*" * 50, "resCookie", "*" * 50)
    print(res_cookies)

    print("*" * 50, "cookie", "*" * 50)
    print(cookies)

    print("*" * 50, "params", "*" * 50)
    print(params)

    cookies["sno"] = stun
    cookies["stdno"] = stun
    cookies["f"] = "12310"
    cookies["su"] = "3"

    ctck = get_ticket(response)
    params = (
        ("r", "0.08286821317886972"),
        ("fid", "0;12310"),
        ("b", "10"),
        ("l", "1"),
        ("tck", save_tick),
        ("lastm", "20180201081222"),
    )

    headers = {
        "Host": "golestan.ikiu.ac.ir",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "575",
        "Origin": "https://golestan.ikiu.ac.ir",
        "Dnt": "1",
        "Referer": "https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON"
        "/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx?r=0.08286821317886972&fid=0%3b12310&b=10&l=1&tck"
        "=6123BBB3-7555-49&&lastm=20180201081222",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "frame",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Te": "trailers",
    }

    data = (
        f"__VIEWSTATE=qxK%2FppR35p5Aud2d23a%2FzBn0bVp1IbJ3fCjyBF0z7P%2BcWa149tMd2W3IPjiKz"
        f"%2FQgblrupixd0OeDtIT9ZdnhdeL8cB2%2FFDcW9qBhJ8WXskwUF7J3lSqbzmxGnF1NVKudV1T270p51Uk%2FL1llMj9hCQ%3D%3D"
        f"&__VIEWSTATEGENERATOR=6AC8DB9B&__EVENTVALIDATION"
        f"=kqy8QEHTvRp1tGzItQv8Zw7V0gg9FSEoYTb0Tuys5EWy1zJ49l14RMA9YVoi7OGATV2Wc4TdXhKNHzU4mYPxbu86iw75hcLx6jSdCNcP1LNBlw1jwrb6x5bhcEPIRSkph7QSNYldljuklZSaP4u%2BaplVnRZMITqO0xknPzR0wKh1lzumRetFMreciDVoKW22xaTEBm0SFhNYaE0%2F6LfnnvIA84YYYr4WYxHT6nSiQ9WyAu%2FHCgHeNd%2BxOQnYRIN7umbWtZqMX58%2F00UyS1tH0Q%3D%3D&Fm_Action=08&Frm_Type=0&Frm_No=&TicketTextBox={ctck}&XMLStdHlp=&TxtMiddle=%3Cr+F41251%3D%22{stun}%22%2F%3E&ex="
    )

    ## Fifth request - second
    response = s.post(
        "https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx",
        headers=headers,
        params=params,
        cookies=cookies,
        data=data,
    )

    print("*" * 50, "Fifth request - second", "*" * 50)
    print(response.text)

    print("*" * 50, "resCookie", "*" * 50)
    print(res_cookies)

    print("*" * 50, "cookie", "*" * 50)
    print(cookies)

    print("*" * 50, "params", "*" * 50)
    print(params)

    try:
        res = re.findall("T01XML='(.*)';", response.content.decode("utf-8"))[0]
    except:
        print("You've got limited! try again later.")
        json_response[
            "status"
        ] = "شما بیش از این مجاز به گرفتن این اطلاعات از گلستان نیستید! 1 ساعت دیگر دوباره امتحان کنید."
        return json_response

    if "دسترسي به اطلاعات مورد نظر را نداريد" in response.text:
        json_response[
            "status"
        ] = "شما بیش از این مجاز به گرفتن این اطلاعات از گلستان نیستید! 1 ساعت دیگر دوباره امتحان کنید."
        return json_response

    faculty, major, grade = get_grade_faculty_major(response)
    soup = read_data(res)
    terms = soup.find_all("n", attrs={"f4455": True})
    latest_term = get_pending_term(terms)
    print(latest_term)
    user_info = get_user_info(terms, latest_term, stun, faculty, major, grade)
    user_data = get_user_grades(user_info, s, session, response, res_cookies["u"], res_cookies["lt"], stun)
    user.save()
    return user_data
