import base64
import re
import urllib.parse
from ast import literal_eval as make_tuple
from typing import Any
from .captcha_solver import get_captcha_text
import requests
from bs4 import BeautifulSoup

from .models import Student


def read_data(xml):
    return BeautifulSoup(xml, "lxml")


def get_header(kwargs=None):
    if kwargs is None:
        kwargs = {}
    header = {
        "Host": "golestan.ikiu.ac.ir",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://golestan.ikiu.ac.ir",
        "Dnt": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "frame",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Te": "trailers",
    }
    for key, value in kwargs.items():
        header[key] = value
    return header


def get_data(url="", optional_attrs=None, headers=None, session_id=None, response=None):
    if headers is None:
        headers = {}
    if optional_attrs is None:
        optional_attrs = {}
    if not response:
        response = requests.get(
            url,
            cookies={"ASP.NET_SessionId": session_id} if session_id else {},
            headers=get_header(headers),
        )
    response = response.content.decode("utf-8")
    inputs = read_data(response).find_all("input", attrs={"id": True, "value": True})
    attrs = {i["id"]: i["value"] for i in inputs} | optional_attrs
    return "&".join([f"{k}={urllib.parse.quote_plus(v)}" for k, v in attrs.items()])


def replace_arabic_with_persian(text):
    # Define a translation table for Arabic to Persian characters
    table = {"ي": "ی", "ك": "ک"}
    for key, value in table.items():
        text = text.replace(key, value)
    return text


def get_pending_term(terms):
    latest_index = -1
    for index, term in enumerate(terms):
        if term["f4455"] == "مشغول به تحصيل _ عادي":
            latest_index = index
    if latest_index == -1:
        latest_index = index
    return latest_index


def get_grade_faculty_major(response):
    script = BeautifulSoup(response.content, "html.parser").find_all("script")[0].string

    def extract_value(pattern):
        match = re.search(pattern, script)
        if match:
            return replace_arabic_with_persian(match.group(1))
        return None

    faculty = extract_value("F61151 = \\'(.*?)\\';")
    major = extract_value("F17551 = \\'(.*?)\\';")
    grade = extract_value("F41301 = \\'(.*?)\\';")
    grade_type = extract_value("F41351 = \\'(.*?)\\';")

    return faculty, major, grade + "-" + grade_type


def get_grades(courses):
    grades = []
    for course in courses:
        course_json = {
            "name": replace_arabic_with_persian(course["f0200"].strip()),
            "nomre": course["f3945"].strip(),
            "type": replace_arabic_with_persian(course["f3952"].strip()),
            "vahed": course["f0205"].strip(),
            "natije_nomre": replace_arabic_with_persian(course["f3965"].strip()),
            "vaziat_nomre": replace_arabic_with_persian(course["f3955"].strip()),
            "eteraz": replace_arabic_with_persian(course["tip_f3945"].strip()),
            "vaziat_dars": replace_arabic_with_persian(course["f3940"].strip()),
        }
        grades.append(course_json)

    return grades


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


def get_user_grades(user_info, s, session, response, u, lt, Stun, fourth_request_url):
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

    header: dict[str, str | Any] = {
        "Content-Length": "595",
        "Referer": fourth_request_url,
    }
    headers = get_header(header)

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

        attrs: dict[str, str | Any] = {
            "Fm_Action": "80",
            "Frm_Type": "0",
            "Frm_No": "",
            "TicketTextBox": ctck,
            "XMLStdHlp": "",
            "TxtMiddle": f'<r F41251="{Stun}" F43501="{term}"/>',
            "ex": "",
        }

        data = get_data(response=response, optional_attrs=attrs)

        response = s.post(
            fourth_request_url,
            headers=headers,
            params=params,
            cookies=cookies,
            data=data,
        )

        res = re.findall("T01XML='(.*)';", response.content.decode("utf-8"))[0]
        courses = read_data(res).find_all("n")[3:]
        print(f'{courses=}')
        course_data = get_grades(courses)
        if term == last_term:
            if not user_info["summery"]["data"][index]["moaddel"]:
                user_info["summery"]["data"][index]["moaddel"] = current_term_gpa(course_data)

        user_info[term] = course_data

    return user_info


def get_user_info(terms, latest_term, Stun, faculty, major, grade):
    global Name
    term = terms[latest_term]
    user_info = {}
    user_data = {}

    user_data["data"] = [
        {"term": t["f4350"].strip(), "moaddel": t["f4360"].strip(), "vahed": t["f4365"].strip()} for t in terms
    ]
    user_data["Allterms"] = [t["f4350"].strip() for t in terms[: latest_term + 1]]
    user_data["Voroodi"] = "1" + user_data["Allterms"][0][:-1]
    user_data["term"] = term["f4350"].strip()
    user_data["termYear"] = term["f4350"].strip()
    user_data["akhzShode"] = term["cumget"].strip()
    user_data["passShode"] = term["cumpas"].strip()
    user_data["moaddelKol"] = term["cumgpa"].strip()
    user_data["name"] = " ".join(Name)
    user_data["stun"] = Stun.strip()
    user_data["faculty"] = faculty.strip()
    user_data["major"] = major.strip()
    user_data["grade"] = grade.strip()
    user_info["summery"] = user_data

    return user_info


def get_ticket(response):
    return (
        BeautifulSoup(response.content, "html.parser")
        .find_all("input", attrs={"id": "TicketTextBox"})[0]
        .attrs["value"]
    )


def get_user_name(response):
    name = (
        BeautifulSoup(response.content, "html.parser").find_all("input", attrs={"name": "TxtMiddle"})[0].attrs["value"]
    )
    name = re.search(r'<F80501 val="(.*)" /><F80551 val="(.*)" /><F83171', name)
    return replace_arabic_with_persian(name.group(1)), replace_arabic_with_persian(name.group(2))


def get_seq(response):
    return make_tuple(re.findall("parent.Commander.SavAut(.*?);", response.content.decode("utf-8"))[0])[6]


def get_session_id(response):
    return response.cookies.get_dict()["ASP.NET_SessionId"]


def get_captcha_image():
    response = requests.get('https://golestan.ikiu.ac.ir/_templates/unvarm/unvarm.aspx', params={'typ': '1'})
    session = get_session_id(response)
    cookies = {
        'ASP.NET_SessionId': session,
        'u': '',
        'lt': '',
    }
    response = requests.get('https://golestan.ikiu.ac.ir/Forms/AuthenticateUser/captcha.aspx', cookies=cookies)
    return session, base64.b64encode(response.content).decode('utf-8')


def login(stun, password):
    global Name
    login_url = "https://golestan.ikiu.ac.ir/Forms/AuthenticateUser/AuthUser.aspx"

    try:
        user = Student.objects.get(stun=stun)
        user.save()
    except:
        user = Student(stun=stun)

    header: dict[str, str] = {
        "Content-Length": "585",
    }
    headers = get_header(header)
    response = ""

    retry_count = 0
    while retry_count < 5:
        session_id, captcha_image = get_captcha_image()
        captcha = get_captcha_text(captcha_image)
        cookies = {
            "u": "",
            "lt": "",
            "su": "",
            "ft": "",
            "f": "",
            "seq": "",
            'ASP.NET_SessionId': session_id,
        }

        attrs: dict[str, str | Any] = {
            "TxtMiddle": f'<r F51851="" F80351="{stun}" F80401="{password}" F51701="{captcha}" F83181=""/>',
            "Fm_Action": "09",
            "Frm_Type": "",
            "Frm_No": "",
            "TicketTextBox": "",
        }
        data = get_data(url=login_url, optional_attrs=attrs)
        # First request
        s = requests.Session()
        response = s.post(login_url, headers=headers, data=data, cookies=cookies)

        print("*" * 50, "First request:", "*" * 50)
        print(response.text)

        if "آخرين ورود" in response.text:
            break
        else:
            retry_count += 1

    json_response = {}
    try:
        ctck = get_ticket(response)
    except:
        json_response["status"] = "نام کاربری/رمز عبور اشتباه است!"
        return json_response

    Name = get_user_name(response)
    full_name = Name[0] + " " + Name[1]
    user.name = full_name
    user.save()

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

    # Second request
    second_request_url = "https://golestan.ikiu.ac.ir/Forms/F0213_PROCESS_SYSMENU/F0213_01_PROCESS_SYSMENU_Dat.aspx"
    response = s.get(
        second_request_url,
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

    attrs = {
        "Fm_Action": "00",
        "Frm_Type": "",
        "Frm_No": "",
        "TicketTextBox": ctck,
        "XMLStdHlp": "",
        "TxtMiddle": "<r/>",
        "ex": "",
    }

    data = get_data(response=response, optional_attrs=attrs)

    header = {
        "Content-Length": "2551",
        "Referer": "https://golestan.ikiu.ac.ir/Forms/F0202_PROCESS_REP_FILTER/F0202_01_PROCESS_REP_FILTER_DAT.ASPX",
    }
    headers1 = get_header(header)

    # Third request - second request post
    response = s.post(
        second_request_url,
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

    header = {
        "Referer": "https://golestan.ikiu.ac.ir/_Templates/Commander.htm",
    }
    headers = get_header(header)

    # Fourth request
    fourth_request_url = (
        "https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx"
    )
    response = s.get(
        fourth_request_url,
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

    header = {
        "Content-Length": "549",
        "Referer": fourth_request_url,
    }
    headers = get_header(header)

    ctck = get_ticket(response)
    params = (
        ("r", "0.8500803687206074"),
        ("fid", "0;12310"),
        ("b", "10"),
        ("l", "1"),
        ("tck", save_tick),
        ("lastm", "20230514110830"),
    )
    attrs["TicketTextBox"] = ctck
    data = get_data(response=response, optional_attrs=attrs)

    # Fifth request
    response = s.post(
        fourth_request_url,
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

    header = {
        "Content-Length": "575",
        "Referer": fourth_request_url,
    }
    headers = get_header(header)

    attrs = {
        "Fm_Action": "08",
        "Frm_Type": "0",
        "Frm_No": "",
        "TicketTextBox": ctck,
        "XMLStdHlp": "",
        "TxtMiddle": f'<r F41251="{stun}"/>',
        "ex": "",
    }

    data = get_data(response=response, optional_attrs=attrs)

    # Fifth request - second
    response = s.post(
        fourth_request_url,
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
    user_info = get_user_info(terms, latest_term, stun, faculty, major, grade)
    user_data = get_user_grades(
        user_info, s, session, response, res_cookies["u"], res_cookies["lt"], stun, fourth_request_url
    )
    user.total_tries += 1
    user.save()
    return user_data
