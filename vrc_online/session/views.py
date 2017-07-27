import warnings

from django.conf import settings
# Avoid shadowing the login() and logout() views below.
from django.contrib import messages
from django.contrib.auth import (
    get_user_model, update_session_auth_hash
)
from django.contrib.auth.forms import (
    PasswordResetForm, SetPasswordForm, PasswordChangeForm
)
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.contrib.auth import logout, login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url, render, redirect
from django.utils.encoding import force_text
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views import View
from django.template.response import TemplateResponse
from django.template.loader import render_to_string

from .tokens import account_activation_token
from .forms import SignUpForm, ProfileForm, ContactForm


def contact_unsigned(request):
    form_class = ContactForm()
    if request.method == 'POST':
        form = form_class(data=request.POST)

        if form.is_valid():
            contact_name = request.POST.get(
                'contact_name', '')
            contact_email = request.POST.get(
                'contact_email', '')
            form_content = request.POST.get('content', '')
            # Email the profile with the
            # contact information
            template = get_template('contact_template.txt')
            context = Context({
                'contact_name': contact_name,
                'contact_email': contact_email,
                'form_content': form_content,
            })
            content = template.render(context)

            email = EmailMessage(
                "ERC Customer Support",
                content,
                "Your website" + '',
                ['youremail@gmail.com'],
                headers={'Reply-To': contact_email}
            )
            email.send()
            return redirect('session:contact')
    return render(request, 'session/contact_u.html', {
        'form': form_class,
    })


@login_required
def contact(request):
    form_class = ContactForm()
    if request.method == 'POST':
        form = form_class(data=request.POST)

        if form.is_valid():
            contact_name = request.POST.get(
                'contact_name', '')
            contact_email = request.POST.get(
                'contact_email', '')
            form_content = request.POST.get('content', '')
            # Email the profile with the
            # contact information
            template = get_template('contact_template.txt')
            context = Context({
                'contact_name': contact_name,
                'contact_email': contact_email,
                'form_content': form_content,
                "id": request.user.id
            })
            content = template.render(context)

            email = EmailMessage(
                "ERC Customer Support",
                content,
                "Your website" + '',
                ['youremail@gmail.com'],
                headers={'Reply-To': contact_email}
            )
            email.send()
            return redirect('session:contact')

    return render(request, 'session/contact.html', {
        'form': form_class,
    })


class AccountUpdate(LoginRequiredMixin, View):

    def post(self, request):
        print(request.POST)
        _method = request.POST.get("_method", None)
        print(_method)
        if _method == "update":
            account_form = ProfileForm(
                instance=request.user, data=request.POST)
            if account_form.is_valid():
                user = account_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(
                    request, 'Your account was successfully updated!')
                return redirect('session:account-details')
            else:
                form = PasswordChangeForm(instance=request.user)
                messages.error(request, 'Please correct the error below.')
                return render(request, 'session/account_details.html',
                              {"form": form, "account_form": account_form})
        elif _method == "password":
            form = PasswordChangeForm(request.user, data=request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(
                    request, 'Your password was successfully updated!')
                return redirect('session:account-details')
            else:

                account_form = ProfileForm(instance=request.user)
                messages.error(request, 'Please correct the error below.')
                return render(request, 'session/account_details.html',
                              {"form": form, "account_form": account_form})

    def get(self, request):
        form = PasswordChangeForm(request.user)
        account_form = ProfileForm(instance=request.user)
        return render(request, 'session/account_details.html', {
            'form': form,
            'account_form': account_form
        })


def logoutUser(request):
    if request.user and request.user.is_authenticated():
        logout(request)
        return redirect("session:home")
    return redirect("session:login")


def account_activation_sent(request):
    return render(request, 'session/account_activation_sent.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_confirmed = True
        user.save()
        login(request, user)
        return redirect('records:index')
    else:
        return render(request, 'session/account_activation_invalid.html')


class AccountCreation(View):

    def get(self, request):
        form = SignUpForm()
        return render(request, 'session/signup.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Activate Your MySite Account'
            message = render_to_string(
                'session/account_activation_email.html',
                {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
            user.email_user(subject, message)
            return redirect('session:account_activation_sent')
        return render(request, 'session/signup.html', {'form': form})


def about(request):
    return render(request, 'session/about.html')


class HomeView(View):

    def get(self, request):
        if request.user:
            if request.user.is_authenticated():
                return redirect('records:index')
        return render(request, "session/home.html")


@csrf_protect
def password_reset(request, is_admin_site=False,
                   template_name='registration/password_reset_form.html',
                   email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=PasswordResetForm,
                   token_generator=default_token_generator,
                   post_reset_redirect=None,
                   from_email=None,
                   current_app=None,
                   extra_context=None,
                   html_email_template_name=None):
    if post_reset_redirect is None:
        post_reset_redirect = reverse('session:password_reset_done')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': token_generator,
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': subject_template_name,
                'request': request,
                'html_email_template_name': html_email_template_name,
            }
            if is_admin_site:
                warnings.warn(
                    "The is_admin_site argument to "
                    "django.contrib.auth.views.password_reset() is deprecated "
                    "and will be removed in Django 1.10."
                )
                opts = dict(opts, domain_override=request.get_host())
            form.save(**opts)
            return HttpResponseRedirect(post_reset_redirect)
    else:
        form = password_reset_form()
    context = {
        'form': form,
        'title': _('Password reset'),
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)


@sensitive_post_parameters()
@never_cache
def password_reset_confirm(request, uidb64=None, token=None,
                           template_name='registration/password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None,
                           current_app=None, extra_context=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    UserModel = get_user_model()
    assert uidb64 is not None and token is not None  # checked by URLconf
    if post_reset_redirect is None:
        post_reset_redirect = reverse('session:password_reset_complete')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    try:
        # urlsafe_base64_decode() decodes to bytestring on Python 3
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        title = _('Enter new password')
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(post_reset_redirect)
        else:
            form = set_password_form(user)
    else:
        validlink = False
        form = None
        title = _('Password reset unsuccessful')
    context = {
        'form': form,
        'title': title,
        'validlink': validlink,
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)


def password_reset_complete(request,
                            template_name='registration/password_reset_complete.html',
                            current_app=None, extra_context=None):
    context = {
        'login_url': resolve_url(settings.LOGIN_URL),
        'title': _('Password reset complete'),
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)


def password_reset_done(request,
                        template_name='registration/password_reset_done.html',
                        current_app=None, extra_context=None):
    context = {
        'title': _('Password reset sent'),
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)
