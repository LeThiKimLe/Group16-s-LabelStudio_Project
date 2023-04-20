"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import uuid
from time import time

from django import forms
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import auth
from django.urls import reverse
from django.core.files.images import get_image_dimensions

from organizations.models import Organization, PendingMember, Role
from core.utils.contextlog import ContextLog
from core.utils.common import load_func


def hash_upload(instance, filename):
    filename = str(uuid.uuid4())[0:8] + '-' + filename
    return settings.AVATAR_PATH + '/' + filename


def check_avatar(files):
    images = list(files.items())
    if not images:
        return None

    filename, avatar = list(files.items())[0]  # get first file
    w, h = get_image_dimensions(avatar)
    if not w or not h:
        raise forms.ValidationError("Can't read image, try another one")

    # validate dimensions
    max_width = max_height = 1200
    if w > max_width or h > max_height:
        raise forms.ValidationError('Please use an image that is %s x %s pixels or smaller.'
                                    % (max_width, max_height))

    # validate content type
    main, sub = avatar.content_type.split('/')
    if not (main == 'image' and sub.lower() in ['jpeg', 'jpg', 'gif', 'png']):
        raise forms.ValidationError(u'Please use a JPEG, GIF or PNG image.')

    # validate file size
    max_size = 1024 * 1024
    if len(avatar) > max_size:
        raise forms.ValidationError('Avatar file size may not exceed ' + str(max_size/1024) + ' kb')

    return avatar

# TODO-Sửa chỗ này để phân quyền
def save_user(request, next_page, user_form, tokenn=None):
    """ Save user instance to DB
    """
    # Chỗ này lưu user trước
    user = user_form.save()
    role = Role.objects.get(name='Owner')
    user.username = user.email.split('@')[0]
    # Lưu user vào htx_user (database)
    user.save()
    # H tới phần thêm vào tổ chức
    if Organization.objects.exists():
        org = Organization.objects.get(token=tokenn)
        # Xác định xem email đã được add vào trong tổ chức chưa
        if PendingMember.objects.filter(email=user.email, organization_id=org.pk).exists():
            # Xóa khỏi pending member và lấy role
            role= (PendingMember.objects.get(email=user.email, organization_id=org.pk))
            org.active_pending_member(user.email)

    else:
        # Đối với owner, tạo mới 1 tổ chức
        org = Organization.create_organization(created_by=user, title='Label Studio')
    # Thêm vào organise member

    org.add_user(user, role)
    # TODO Thuộc tính này chỉ khi một member thuộc 1 organization, fix sau
    user.active_organization = org
    user.role = role
    user.save(update_fields=['active_organization', 'role'])

    request.advanced_json = {
        'email': user.email, 'allow_newsletters': user.allow_newsletters,
        'update-notifications': 1, 'new-user': 1
    }

    redirect_url = next_page if next_page else reverse('projects:project-index')
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect(redirect_url)

# Hàm này để lưu user khi đăng ký vào tổ chức, cũng cần sửa
def proceed_registration(request, user_form, organization_form, next_page, token=None):
    """ Register a new user for POST user_signup
    """
    # save user to db
    save_user = load_func(settings.SAVE_USER)
    response = save_user(request, next_page, user_form, token)
    return response


def login(request, *args, **kwargs):
    request.session['last_login'] = time()
    return auth.login(request, *args, **kwargs)


    