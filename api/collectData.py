import re
import urllib.parse
from ast import literal_eval as make_tuple

import requests
from bs4 import BeautifulSoup

from .models import student


def readData(xml):
	soup = BeautifulSoup(xml, 'lxml')
	return soup

def getPendingTerm(terms):
	latest = 0
	for index, term in enumerate(terms):
		if term['f4455'] == 'مشغول به تحصيل _ عادي':
			latest = index
	return latest

def getGrades(courses):
	ar = []
	for course in courses:
		coursesJson = {}
		coursesJson['name'] = course['f0200'].strip()
		coursesJson['nomre'] = course['f3945'].strip()
		coursesJson['type'] = course['f3952'].strip()
		coursesJson['vahed'] = course['f0205'].strip()
		ar.append(coursesJson)

	return ar


def getUserGrades(userInfo, s, session, response, u, lt, Stun):
	cookies = {
		'u': u,
		'lt': lt,
		'su': '3',
		'ft': '0',
		'f': '12310',
		'seq': str(getSeq(response)),
		'ASP.NET_SessionId': session,
		'sno': Stun,
		'stdno': Stun,
	}

	headers = {
		'Host': 'golestan.ikiu.ac.ir',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Content-Type': 'application/x-www-form-urlencoded',
		'Content-Length': '595',
		'Origin': 'https://golestan.ikiu.ac.ir',
		'Dnt': '1',
		'Referer': 'https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx?r=0.41827066214011355&fid=0%3b12310&b=10&l=1&tck=9D871E0D-BE1C-4E&&lastm=20180201081222',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'frame',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Te': 'trailers',
	}

	for index, term in enumerate(userInfo['summery']['Allterms']):
		ctck = getTicket(response)
		params = (
			('r', '0.41827066214011355'),
			('fid', '0;12310'),
			('b', '10'),
			('l', '1'),
			('tck', ctck),
			('lastm', '20180201081222'),
		)

		data = f'__VIEWSTATE=%2FwEPDwUKMjExODY3MDQ1MGRkqTooH%2BaGmNBUy44EHeUKu%2BW01Hwb7DLrGPWvEPXq%2FW%2BO%2FlIiFC3htijD8r4v3NhncWVwdVNwefzUP8TqplMEyA%3D%3D&__VIEWSTATEGENERATOR=6AC8DB9B&__EVENTVALIDATION=%2FwEdAAdVCUcuqSM8fm0iJFI1%2FIdqP8uVt%2B%2BIGse5yjzuSxmAtwJG302dI8ANIU5vM1WrdKE9lJCizcSsDB8OaGU3AfioSxPoV%2BZXtQtDuP8UYzmw7oxw4gRCwvpu3X6T9xy%2B1mrgAsbxLtmIuUmpKy5cGyMbLoMo0rMQsHIjjbSg0NWsgq3ZcERA1erCfXKylX1SdMvie1uYBsiht%2BZk1htJCvcguGNIYx9yD1KkKYOMil7Clw%3D%3D&Fm_Action=80&Frm_Type=0&Frm_No=&TicketTextBox={ctck}&XMLStdHlp=&TxtMiddle=%3Cr+F41251%3D%22{Stun}%22+F43501%3D%22{term}%22%2F%3E&ex='

		response = s.post('https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx', headers=headers, params=params, cookies=cookies, data=data)

		res = re.findall("T01XML='(.*)';", response.content.decode('utf-8'))[0]
		soup = readData(res)
		courses = soup.find_all('n')[3:]
		courseData = getGrades(courses)
		userInfo[term] = courseData

	return userInfo

def getUserInfo(terms, latestTerm, Stun):
	global Name
	term = terms[latestTerm]
	userInfo = {}
	userData = {}
	ar = []
	for t in terms:
		temp = {}
		temp['term'] = t['f4350'].strip()
		temp['moaddel'] = t['f4360'].strip()
		temp['vahed'] = t['f4365'].strip()
		ar.append(temp)
		
	userData['data'] = ar
	userData['Allterms'] = [t['f4350'].strip() for index, t in enumerate(terms) if index <= latestTerm]
	userData['Voroodi'] = '1' + userData['Allterms'][0][:-1]
	userData['term'] = term['f4350'].strip()
	userData['termYear'] = term['f4350'].strip()
	userData['akhzShode'] = term['cumget'].strip()
	userData['passShode'] = term['cumpas'].strip()
	userData['moaddelKol'] = term['cumgpa'].strip()
	userData['name'] = Name[0] + ' ' + Name[1]
	userData['stun'] = Stun.strip()
	userInfo['summery'] = userData
	return userInfo

def getTicket(response):
	soup = BeautifulSoup(response.content, 'html.parser')
	ctck = soup.find_all('input', attrs={'id':'TicketTextBox'})[0].attrs['value']
	return ctck


def gtUserName(response):
	soup = BeautifulSoup(response.content, 'html.parser')
	Name = soup.find_all('input', attrs={'name':'TxtMiddle'})[0].attrs['value']
	Name = re.search(r'<F80501 val="(.*)" /><F80551 val="(.*)" /><F83171', Name)
	return (Name.group(1), Name.group(2))

def checkReponse(response):
	print(response.content.decode('utf-8'))

def getSeq(response):
	res = make_tuple(re.findall('parent.Commander.SavAut(.*?);', response.content.decode('utf-8'))[0])
	return res[6]

def values(response):
	res = make_tuple(re.findall('parent.Commander.SavAut(.*?);', response.content.decode('utf-8'))[0])
	return res

def getSessionID(response):
	return response.cookies.get_dict()['ASP.NET_SessionId']

def login(Stun, password):
	global Name
	loginUrl = 'https://golestan.ikiu.ac.ir/Forms/AuthenticateUser/AuthUser.aspx'

	try:
		user = student.objects.get(stun=Stun)
	except:
		user = student(stun=Stun)

	jsonResponse = {}
	captcha = ''
	password = urllib.parse.quote_plus(password)

	cookies = {
		'u': '',
		'lt': '',
		'su': '',
		'ft': '',
		'f': '',
		'seq': '',
	}

	headers = {
		'Host': 'golestan.ikiu.ac.ir',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Content-Type': 'application/x-www-form-urlencoded',
		'Content-Length': '585',
		'Origin': 'https://golestan.ikiu.ac.ir',
		'Dnt': '1',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'frame',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Te': 'trailers',
	}

	data = f'__VIEWSTATE=%2FwEPDwUKMjA2NTYzNTQ5MmRk3pMVc3vrMpmJPeFlNuTZNAqnZ1IuvBAh7F6ibaOvjLcRmUq1Bo93homnh5DYRQi8BRW5Rzfi%2BYZuKAERQqxuQQ%3D%3D&__VIEWSTATEGENERATOR=6A475423&__EVENTVALIDATION=%2FwEdAAZLlyHuYR3BLALr37%2Bc2m3n4ALG8S7ZiLlJqSsuXBsjGz%2FLlbfviBrHuco87ksZgLcCRt9NnSPADSFObzNVq3ShPZSQos3ErAwfDmhlNwH4qEsT6FfmV7ULQ7j%2FFGM5sO5GzNDLxCLDFj1724Jc3Y%2BlrbM5jHMQ3800JLSzB8cvT0PujcljIJ7JpjSJMqHuPBKXt1c%2B%2BVTuIBSvjVJnUw2o&TxtMiddle=%3Cr+F51851%3D%22%22+F80401%3D%22{password}%22+F80351%3D%22{Stun}%22+F51701%3D%22{captcha}%22+F83181%3D%22%22%2F%3E&Fm_Action=09&Frm_Type=&Frm_No=&TicketTextBox='

	## First request
	s = requests.Session()
	response = s.post(loginUrl, headers=headers, data=data, cookies=cookies)

	try:
		ctck = getTicket(response)
	except Exception as e:
		jsonResponse['status'] = 'نام کاربری/رمز عبور اشتباه است!'
		return jsonResponse

	Name = gtUserName(response)
	fullName = Name[0] + ' ' + Name[1]
	user.name = fullName

	resCookies = response.cookies.get_dict()
	cookies = {
		'u': resCookies['u'],
		'lt': resCookies['lt'],
		'su': '0',
		'ft': '0',
		'f': '1',
		'seq': str(getSeq(response)),
	}

	params = (
		('r', '0.4994271499377073'),
		('fid', '0;11130'),
		('b', ''),
		('l', ''),
		('tck', ctck),
		('lastm', '20090829065642'),
	)

	## Second request
	response = s.get('https://golestan.ikiu.ac.ir/Forms/F0213_PROCESS_SYSMENU/F0213_01_PROCESS_SYSMENU_Dat.aspx', params=params, cookies=cookies)

	try:
		session = getSessionID(response) 
	except Exception as e:
		jsonResponse['status'] = 'بعلت لاگین بیش از حد توسط گلستان محدود شده اید. 1 ساعت دیگر دوباره وارد شوید.'
		return jsonResponse

	ctck = getTicket(response)
	resCookies = response.cookies.get_dict()
	cookies = {
		'u': resCookies['u'],
		'lt': resCookies['lt'],
		'su': '0',
		'ft': '0',
		'f': '11130',
		'seq': str(getSeq(response)),
		'ASP.NET_SessionId': session,
		'ctck':ctck
	}

	data = f'__VIEWSTATE=%2FwEPDwUKMTg5NzY5NjczOGRkYUDVSrQ4gKKlXHZpC7vZcGlJgTLPsZIAvGSZ%2FIZFhZ%2F2SOqFiNzxPYofyD9Tfb9mtFcWafaiyEDeKi1If0vTKA%3D%3D&__VIEWSTATEGENERATOR=25DF661B&__EVENTVALIDATION=%2FwEdAAc7lghiqMRe6gTOwdPMXHqGP8uVt%2B%2BIGse5yjzuSxmAtwJG302dI8ANIU5vM1WrdKE9lJCizcSsDB8OaGU3AfioSxPoV%2BZXtQtDuP8UYzmw7oxw4gRCwvpu3X6T9xy%2B1mrgAsbxLtmIuUmpKy5cGyMbaThuHd7TyAdgVN58OJLAXj%2BRMPndAdlLJTU%2B9lWfcDuOzzgqynWcQ9v8%2BRWa9N77dcG4tx9eUPLG4LOeVRvIbQ%3D%3D&Fm_Action=00&Frm_Type=&Frm_No=&TicketTextBox={ctck}&XMLStdHlp=&TxtMiddle=%3Cr%2F%3E&ex='

	headers1 = {
		'Host': 'golestan.ikiu.ac.ir',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Content-Type': 'application/x-www-form-urlencoded',
		'Content-Length': '2551',
		'Origin': 'https://golestan.ikiu.ac.ir',
		'Dnt': '1',
		'Referer': 'https://golestan.ikiu.ac.ir/Forms/F0202_PROCESS_REP_FILTER/F0202_01_PROCESS_REP_FILTER_DAT.ASPX?r=0.75486758742996&fid=1%3b102&b=10&l=1&tck=9691AB60-96A2-43&&lastm=20190829142532',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'frame',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Te': 'trailers',
	}

	## Third request
	response = s.post('https://golestan.ikiu.ac.ir/Forms/F0213_PROCESS_SYSMENU/F0213_01_PROCESS_SYSMENU_Dat.aspx', params=params, cookies=cookies, data=data, headers=headers1)

	ctck = getTicket(response)
	resCookies = response.cookies.get_dict()
	cookies = {
		'u': resCookies['u'],
		'lt': resCookies['lt'],
		'su': '0',
		'ft': '0',
		'f': '11130',
		'seq': str(getSeq(response)),
		'ASP.NET_SessionId': session,
	}


	params = (
		('r', '0.6454015321212107'),
		('fid', '0;12310'),
		('b', '10'),
		('l', '1'),
		('tck', ctck),
		('lastm', '20190829142532'),
	)

	headers = {
		'Host': 'golestan.ikiu.ac.ir',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Referer': 'https://golestan.ikiu.ac.ir/_Templates/Commander.htm',
		'Dnt': '1',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'frame',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Te': 'trailers',
	}

	response = s.get('https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx', headers=headers, params=params, cookies=cookies)

	cookies = {
		'u': resCookies['u'],
		'lt': resCookies['lt'],
		'su': '3',
		'ft': '0',
		'f': '12310',
		'seq': str(getSeq(response)),
		'ASP.NET_SessionId': session,
		'stdno': '',
		'sno': '',
	}

	headers = {
		'Host': 'golestan.ikiu.ac.ir',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Content-Type': 'application/x-www-form-urlencoded',
		'Content-Length': '549',
		'Origin': 'https://golestan.ikiu.ac.ir',
		'Dnt': '1',
		'Referer': 'https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx?r=0.08286821317886972&fid=0;12310&b=10&l=1&tck=6123BBB3-7555-49&&lastm=20180201081222',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'frame',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Te': 'trailers',
	}

	ctck = getTicket(response)
	params = (
		('r', '0.08286821317886972'),
		('fid', '0;12310'),
		('b', '10'),
		('l', '1'),
		('tck', ctck),
		('lastm', '20180201081222'),
	)

	data = f'__VIEWSTATE=%2FwEPDwUKMjExODY3MDQ1MGRkqTooH%2BaGmNBUy44EHeUKu%2BW01Hwb7DLrGPWvEPXq%2FW%2BO%2FlIiFC3htijD8r4v3NhncWVwdVNwefzUP8TqplMEyA%3D%3D&__VIEWSTATEGENERATOR=6AC8DB9B&__EVENTVALIDATION=%2FwEdAAdVCUcuqSM8fm0iJFI1%2FIdqP8uVt%2B%2BIGse5yjzuSxmAtwJG302dI8ANIU5vM1WrdKE9lJCizcSsDB8OaGU3AfioSxPoV%2BZXtQtDuP8UYzmw7oxw4gRCwvpu3X6T9xy%2B1mrgAsbxLtmIuUmpKy5cGyMbLoMo0rMQsHIjjbSg0NWsgq3ZcERA1erCfXKylX1SdMvie1uYBsiht%2BZk1htJCvcguGNIYx9yD1KkKYOMil7Clw%3D%3D&Fm_Action=00&Frm_Type=&Frm_No=&TicketTextBox={ctck}&XMLStdHlp=&TxtMiddle=%3Cr%2F%3E&ex='

	response = s.post('https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx', headers=headers, params=params, cookies=cookies, data=data)

	cookies['sno'] = Stun
	cookies['stdno']= Stun
	cookies['f']= '12310'
	cookies['su']= '3'

	ctck = getTicket(response)
	params = (
		('r', '0.08286821317886972'),
		('fid', '0;12310'),
		('b', '10'),
		('l', '1'),
		('tck', ctck),
		('lastm', '20180201081222'),
	)

	headers = {
		'Host': 'golestan.ikiu.ac.ir',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Content-Type': 'application/x-www-form-urlencoded',
		'Content-Length': '575',
		'Origin': 'https://golestan.ikiu.ac.ir',
		'Dnt': '1',
		'Referer': 'https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx?r=0.08286821317886972&fid=0%3b12310&b=10&l=1&tck=6123BBB3-7555-49&&lastm=20180201081222',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'frame',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Te': 'trailers',
	}

	data = f'__VIEWSTATE=%2FwEPDwUKMjExODY3MDQ1MGRkqTooH%2BaGmNBUy44EHeUKu%2BW01Hwb7DLrGPWvEPXq%2FW%2BO%2FlIiFC3htijD8r4v3NhncWVwdVNwefzUP8TqplMEyA%3D%3D&__VIEWSTATEGENERATOR=6AC8DB9B&__EVENTVALIDATION=%2FwEdAAdVCUcuqSM8fm0iJFI1%2FIdqP8uVt%2B%2BIGse5yjzuSxmAtwJG302dI8ANIU5vM1WrdKE9lJCizcSsDB8OaGU3AfioSxPoV%2BZXtQtDuP8UYzmw7oxw4gRCwvpu3X6T9xy%2B1mrgAsbxLtmIuUmpKy5cGyMbLoMo0rMQsHIjjbSg0NWsgq3ZcERA1erCfXKylX1SdMvie1uYBsiht%2BZk1htJCvcguGNIYx9yD1KkKYOMil7Clw%3D%3D&Fm_Action=08&Frm_Type=0&Frm_No=&TicketTextBox={ctck}&XMLStdHlp=&TxtMiddle=%3Cr+F41251%3D%22{Stun}%22%2F%3E&ex='

	response = s.post('https://golestan.ikiu.ac.ir/Forms/F1802_PROCESS_MNG_STDJAMEHMON/F1802_01_PROCESS_MNG_STDJAMEHMON_Dat.aspx', headers=headers, params=params, cookies=cookies, data=data)

	try:
		res = re.findall("T01XML='(.*)';", response.content.decode('utf-8'))[0]
	except Exception as e:
		print('You got limited! try again later.')
		jsonResponse['status'] = 'شما بیش از این مجاز به گرفتن این اطلاعات از گلستان نیستسد! 1 ساعت دیگر دوباره امتحان کنید.'
		return jsonResponse
	
	soup = readData(res)
	terms = soup.find_all('n')
	latestTerm = getPendingTerm(terms)
	userInfo = getUserInfo(terms, latestTerm, Stun)
	userData = getUserGrades(userInfo, s, session, response, resCookies['u'], resCookies['lt'], Stun)
	user.save()
	return userData
