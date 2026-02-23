from django.shortcuts import redirect

def home_redirect(request):
    return redirect("flota:colectivo_list")
