import time
from datetime import datetime

from django.http import HttpResponse, JsonResponse

from .collect_data import login
from .models import get_rate_limit, Student

# Create your views here.


def rate_limit(request, stun, debug):
    if debug == "nolimit":
        return True, 0
    try:
        user = Student.objects.get(stun=stun)
        now = time.mktime(datetime.now().timetuple())
        last_try = time.mktime(user.last_try.timetuple())
        limit = get_rate_limit() * 60
        delta = (last_try + limit - now) / 60
        if now < last_try + limit:
            return False, delta
        else:
            return True, 0
    except:
        return True, 0


def api(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed.", status=405)

    if request.POST.get("stun"):
        stun = request.POST.get("stun")
    else:
        data = {"status": "نام کاربری ارسال نشده است."}
        return JsonResponse(data)

    if request.POST.get("password"):
        password = request.POST.get("password")
    else:
        data = {"status": "رمزعبور ارسال نشده است."}
        return JsonResponse(data)

    res, remain = rate_limit(request, stun, request.POST.get("debug"))
    if not res:
        if int(remain) == 0:
            data = {"status": f"کمتر از 1 دقیقه‌ی دیگر دوباره امتحان کنید."}
        else:
            data = {"status": f"{int(remain)} دقیقه دیگر امتحان کنید."}
        return JsonResponse(data)
    else:
        data = login(stun, password)
        return JsonResponse(data)
