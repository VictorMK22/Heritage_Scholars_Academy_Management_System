from django.http import HttpResponseForbidden
from functools import wraps

def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if not request.user.is_student():
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if not request.user.is_teacher():
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def guardian_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if not request.user.is_guardian():
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view