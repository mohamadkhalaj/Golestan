import time
from datetime import datetime

from django.http import HttpResponse, JsonResponse

from .collectData import login
from .models import get_rate_limit, student

# Create your views here.


def rateLimit(request, Stun, debug):
    if debug == "nolimit":
        return (True, 0)
    try:
        user = student.objects.get(stun=Stun)
        now = time.mktime(datetime.now().timetuple())
        lastTry = time.mktime(user.lastTry.timetuple())
        limit = get_rate_limit() * 60
        delta = (lastTry + limit - now) / 60
        if now < lastTry + limit:
            return (False, delta)
        else:
            return (True, 0)
    except:
        return (True, 0)


def Api(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed.", status=405)

    if request.POST.get("stun"):
        Stun = request.POST.get("stun")
    else:
        data = {"status": "نام کاربری ارسال نشده است."}
        return JsonResponse(data)

    if request.POST.get("password"):
        password = request.POST.get("password")
    else:
        data = {"status": "رمزعبور ارسال نشده است."}
        return JsonResponse(data)

    res, remain = rateLimit(request, Stun, request.POST.get("debug"))
    if not res:
        if int(remain) == 0:
            data = {"status": f"کمتر از 1 دقیقه‌ی دیگر دوباره امتحان کنید."}
        else:
            data = {"status": f"{int(remain)} دقیقه دیگر امتحان کنید."}
        return JsonResponse(data)
    else:
        data = login(Stun, password)
        return JsonResponse(data)
