from django.http import HttpResponse
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth  import authenticate, login
from ManageUsers.forms import UserForm, UserProfileForm, LoginForm, DisplayUserForm, PrivacyForm, DisplayProfileForm, UserEditForm, SubmitForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from ManageIdea.models import Idea
from IBID.functions import get_ip_instance, Object
from ManageUsers.models import UserProfile, UserProfilePrivacy
from guardian.shortcuts import assign_perm, get_perms
from ManageIdea.views import assign_permissions
import Home
import re


@login_required
def userprofile(request,User_id):
	user = get_object_or_404(User,pk = User_id)
	userprofile = get_object_or_404(UserProfile,user=user)
	privacy = get_object_or_404(UserProfilePrivacy,instance=userprofile)
	view_user_form = DisplayUserForm(instance = user)
	view_profile_form = DisplayProfileForm(instance = userprofile)
	ideas=Idea.objects.filter(owner=user)
	perms = get_perms(request.user,userprofile)
	if 'edit' in perms:
		edit_profile = user.id
	else:
		edit_profile=False
	if 'view' in perms:
		return render(request, 'ManageUsers/profile.html', {'view_user_form':view_user_form,'view_profile_form':view_profile_form, 'ideas':ideas,'edit_profile':edit_profile})
	else:
		view_profile_form=DisplayProfileForm(instance=get_ip_instance(privacy,UserProfile))
		return render(request, 'ManageUsers/profile.html', {'view_profile_form':view_profile_form,'view_user_form':view_user_form, 'ideas':ideas, 'edit_profile':edit_profile})


def logout_user(request):
	logout(request)
	return render(request, 'ManageUsers/logout.html')

def register(request):
	registered = False

	if request.method == 'POST':
		#grab information form from the POST data
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)
		privacy_form = PrivacyForm(data=request.POST)
		submit_form=SubmitForm()		
		#if the form is valid
		if user_form.is_valid() and profile_form.is_valid() and privacy_form.is_valid():
			user = user_form.save()

			#hash password and save
			user.set_password(user.password)
			user.save()

			# Now sort out the UserProfile instance.
			# Since we need to set the user attribute ourselves, we set commit=False.
			# This delays saving the model until we're ready to avoid integrity problems.
			profile = profile_form.save(commit=False)
			profile.user=user
			profile.save()
			privacy = privacy_form.save(commit=False)
			privacy.instance = profile
			privacy.save()
			assign_permissions(user=profile.user,instance=profile)


			#save profile
			profile.save()

			#template registration was successful
			registered=True

			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username=username, password=password)
			login(request, user)			
			return HttpResponseRedirect(reverse('ManageUsers:userprofile',args=[user.id,]))
		else:
			print( user_form.errors, profile_form.errors)
			return render(request, 'ManageUsers/register.html', {'user_form': user_form, 'profile_form': profile_form,'privacy_form':privacy_form, 'submit_form':submit_form, 'registered': registered})
	# GET
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()
		privacy_form = PrivacyForm()
		submit_form=SubmitForm()

		#render template
		return render(request, 'ManageUsers/register.html', {'user_form': user_form, 'profile_form': profile_form,'privacy_form':privacy_form, 'submit_form':submit_form, 'registered': registered})

def user_login(request):
	if request.method == 'POST':

		#gather username and passwd from form
		login_form = LoginForm(data=request.POST)

		#validate
		if login_form.is_valid():
			username = login_form.cleaned_data['username']
			password = login_form.cleaned_data['password']

			#authenticate
			user = authenticate(username=username, password=password)

			#if user is a User Object, there is a user and credentials where correct
			#else user == None
			if user:
				#active?
				if user.is_active:
					#log user in
					login(request,user)
					return HttpResponseRedirect(request.POST['next'])
				else:
					return HttpResponse("Your IBID account is inactive")
			else:
				print("Invalid login details: {0}, {1}".format(username, password))
				return HttpResponse("Invalid login details supplied.")

		else:
			print( login_form.errors)
			return render(request, 'ManageUsers/login.html', {'login_form':login_form})

	elif request.method == 'GET':
		#create empty forms to distribute
		login_form = LoginForm()

		if 'next' in request.GET:
			next=request.GET['next']
		else:
			next=reverse('Home:index')
			#render login template
		return render(request,'ManageUsers/login.html',{'login_form':login_form,'next':next})

@login_required
def edit(request, User_id):
	user = get_object_or_404(User,pk = User_id)
	profile= get_object_or_404(UserProfile, user=user)
	privacy=get_object_or_404(UserProfilePrivacy, instance=profile)
	if not 'edit' in get_perms(request.user, profile):
		return HttpResponse('You have no permissions to edit this profile')
	else:
		if request.method == 'POST':
			#grab information form from the POST data
			user_form=UserEditForm(data=request.POST, instance=user)
			profile_form = UserProfileForm(data=request.POST, instance=profile)
			privacy_form = PrivacyForm(data=request.POST, instance=privacy)
			#if the form is valid
			if  user_form.is_valid() and profile_form.is_valid() and privacy_form.is_valid():
				user_form.save()
				profile.save()
				privacy.save()
				return HttpResponseRedirect(reverse('ManageUsers:userprofile', args=[user.id,]))
			else:
				print( profile_form.errors, privacy_form.errors)

		# GET
		else:
			user_form=UserEditForm(instance=user)
			profile_form = UserProfileForm(instance=profile)
			privacy_form = PrivacyForm(instance=privacy)
			submit_form=SubmitForm()
			#render template
			return render(request, 'ManageUsers/edit.html', {'user_form':user_form, 'profile_form': profile_form,'privacy_form':privacy_form, 'submit_form':submit_form})

