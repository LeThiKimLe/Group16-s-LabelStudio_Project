"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import logging
from time import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse
from django.contrib import auth
from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token

from users import forms
from core.utils.common import load_func
from users.functions import login
from core.middleware import enforce_csrf_checks
from users.functions import proceed_registration
from organizations.models import Organization
from organizations.forms import OrganizationSignupForm
from current_instance.save_instance import CurrentInstance


logger = logging.getLogger()


@login_required
def logout(request):
    auth.logout(request)
    if settings.HOSTNAME:
        redirect_url = settings.HOSTNAME
        if not redirect_url.endswith('/'):
            redirect_url += '/'
        return redirect(redirect_url)
    return redirect('/')


@enforce_csrf_checks
def user_signup(request):
    """ Sign up page
    """
    user = request.user
    next_page = request.GET.get('next')
    tokenn = request.GET.get('token')
    next_page = next_page if next_page else reverse('projects:project-index')
    user_form = forms.UserSignupForm()
    organization_form = OrganizationSignupForm()

    if user.is_authenticated:
        return redirect(next_page)

    # make a new user
    # Này thực hiện khi đã điền thông tin và bấm nút gửi
    if request.method == 'POST':
        if Organization.objects.filter(token=tokenn).exists():
            organization = Organization.objects.get(token=tokenn)
            CurrentInstance.set_current_organization(organization)
            
        # Từ chối nếu mã token của organization bị sai
        if settings.DISABLE_SIGNUP_WITHOUT_LINK is True:
            if not(tokenn and organization and tokenn == organization.token):
                raise PermissionDenied()
        else:
            if tokenn and organization and tokenn != organization.token:
                raise PermissionDenied()
        
        # Phần này có 2 th: 1 là người dùng đầu tiên (owner) sẽ tạo tổ chức mặc định là Label-Studio
        #                   2 là các người dùng được cấp quyền bởi owner hoặc các người khác có quyền, khi đó, ng dùng sẽ đc xác thực rồi mới đc đăng ký

        user_form = forms.UserSignupForm(request.POST)
        organization_form = OrganizationSignupForm(request.POST)

        # Sau khi các thông tin được điền hết thì tiến hành đăng ký tài khoản 
        if user_form.is_valid():
            redirect_response = proceed_registration(request, user_form, organization_form, next_page, tokenn)
            if redirect_response:
                return redirect_response

    # Này là khi GET, chỉ trả lại form để điền
    return render(request, 'users/user_signup.html', {
        'user_form': user_form,
        'organization_form': organization_form,
        'next': next_page,
        'token': tokenn,
    })


@enforce_csrf_checks
def user_login(request):
    """ Login page
    """
    user = request.user
    next_page = request.GET.get('next')
    next_page = next_page if next_page else reverse('projects:project-index')
    login_form = load_func(settings.USER_LOGIN_FORM)
    form = login_form()

    if user.is_authenticated:
        return redirect(next_page)

    if request.method == 'POST':
        form = login_form(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if form.cleaned_data['persist_session'] is not True:
                # Set the session to expire when the browser is closed
                request.session['keep_me_logged_in'] = False
                request.session.set_expiry(0)

            # user is organization member
            org_pk = Organization.find_by_user(user).pk
            user.active_organization_id = org_pk
            user.save(update_fields=['active_organization'])
            return redirect(next_page)

    return render(request, 'users/user_login.html', {
        'form': form,
        'next': next_page
    })


@login_required
def user_account(request):
    user = request.user

    if user.active_organization is None and 'organization_pk' not in request.session:
        return redirect(reverse('main'))

    form = forms.UserProfileForm(instance=user)
    token = Token.objects.get(user=user)

    if request.method == 'POST':
        form = forms.UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect(reverse('user-account'))
        
    return render(request, 'users/user_account.html', {
        'settings': settings,
        'user': user,
        'user_profile_form': form,
        'token': token
    })
