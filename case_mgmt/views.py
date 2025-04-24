# case_mgmt/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import *
from .forms import *
import requests
from datetime import datetime
import json
import os
from .utils import build_pdf_content

# case_mgmt/views.py

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'case_mgmt/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, "Passwords don't match")
            return redirect('register')
            
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                role=role,
                password=password1
            )
            login(request, user)
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
    
    return render(request, 'case_mgmt/register.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def home_view(request):
    # Update or create recent cases
    recent_cases = UserRecentCase.objects.filter(user=request.user).order_by('-viewed_at')[:3]
    
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')
        cases = Case.objects.filter(
            models.Q(name__icontains=search_query) | 
            models.Q(case_number__icontains=search_query)
        )
        return render(request, 'case_mgmt/search_results.html', {'cases': cases, 'search_query': search_query})
    
    return render(request, 'case_mgmt/home.html', {
        'recent_cases': recent_cases,
    })

@login_required
def ipfs_connect_view(request):
    if request.method == 'POST':
        form = PinataCredentialsForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_ipfs_connected = True
            user.save()
            messages.success(request, 'Successfully connected to Pinata IPFS')
            return redirect('home')
    else:
        form = PinataCredentialsForm(instance=request.user)
    return render(request, 'case_mgmt/ipfs_connect.html', {'form': form})

@login_required
def create_case_view(request):
    if request.user.role != 'forensic':
        messages.error(request, 'Only forensic users can create cases')
        return redirect('home')
    
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            
            # Log activity
            CaseActivityLog.objects.create(
                case=case,
                user=request.user,
                activity=f"Case created by {request.user.username}"
            )
            
            messages.success(request, 'Case created successfully')
            return redirect('case_detail', case_id=case.id)
    else:
        form = CaseForm()
    return render(request, 'case_mgmt/create_case.html', {'form': form})

@login_required
def case_detail_view(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    # Check if user has access to the case
    if case.case_type == 'private' and request.user not in case.shared_with.all() and request.user != case.created_by:
        messages.error(request, 'You do not have permission to view this case')
        return redirect('home')
    
    # Log this view activity
    CaseActivityLog.objects.create(
        case=case,
        user=request.user,
        activity=f"Viewed case by {request.user.username}"
    )
    
    # Update recent cases
    UserRecentCase.objects.update_or_create(
        user=request.user,
        case=case,
        defaults={'viewed_at': timezone.now()}
    )
    
    # Handle file upload
    if request.method == 'POST' and 'file' in request.FILES:
        if not request.user.is_ipfs_connected:
            messages.error(request, 'Please connect to Pinata IPFS first')
            return redirect('ipfs_connect')
        
        file = request.FILES['file']
        file_name = file.name
        file_type = file_name.split('.')[-1].lower()
        
        try:
            # Upload to Pinata IPFS
            url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
            headers = {
                'pinata_api_key': request.user.pinata_api_key,
                'pinata_secret_api_key': request.user.pinata_secret
            }
            files = {'file': file}
            response = requests.post(url, files=files, headers=headers)
            
            if response.status_code == 200:
                cid = response.json()['IpfsHash']
                CaseFile.objects.create(
                    case=case,
                    file_name=file_name,
                    cid=cid,
                    file_type=file_type
                )
                messages.success(request, 'File uploaded successfully to IPFS')
            else:
                messages.error(request, f'Error uploading file: {response.text}')
        except Exception as e:
            messages.error(request, f'Error uploading file: {str(e)}')
    
    # Handle sharing case
    if request.method == 'POST' and 'share_email' in request.POST:
        share_form = ShareCaseForm(request.POST)
        if share_form.is_valid():
            email = share_form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                case.shared_with.add(user)
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    case=case,
                    message=f"You have been granted access to case: {case.name}"
                )
                
                messages.success(request, f'Case shared successfully with {email}')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User with this email does not exist')
    
    # Handle removing shared user
    if request.method == 'POST' and 'remove_user' in request.POST:
        user_id = request.POST.get('remove_user')
        try:
            user = CustomUser.objects.get(id=user_id)
            case.shared_with.remove(user)
            messages.success(request, f'Removed access for {user.username}')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found')
    
    # Handle disclosure form (for police only)
    if request.method == 'POST' and 'disclosure_form' in request.POST and request.user.role == 'police':
        disclosure_form = DisclosureFormForm(request.POST)
        if disclosure_form.is_valid():
            try:
                # Generate a simple PDF (in a real app, use a proper PDF library)
                form_name = disclosure_form.cleaned_data['form_name']
                pdf_content = f"Disclosure Form\nCase: {case.name}\nVerified by: {request.user.username}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # Upload to Pinata IPFS
                url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
                headers = {
                    'pinata_api_key': request.user.pinata_api_key,
                    'pinata_secret_api_key': request.user.pinata_secret
                }
                files = {'file': ('disclosure.pdf', pdf_content)}
                response = requests.post(url, files=files, headers=headers)
                
                if response.status_code == 200:
                    cid = response.json()['IpfsHash']
                    DisclosureForm.objects.create(
                        case=case,
                        added_by=request.user,
                        form_pdf_cid=cid,
                        form_name=form_name
                    )
                    messages.success(request, 'Disclosure form added successfully')
                else:
                    messages.error(request, f'Error uploading disclosure form: {response.text}')
            except Exception as e:
                messages.error(request, f'Error creating disclosure form: {str(e)}')
    
    # Handle file removal
    if request.method == 'POST' and 'remove_file' in request.POST:
        file_id = request.POST.get('remove_file')
        try:
            file = CaseFile.objects.get(id=file_id, case=case)
            
            # Unpin from Pinata IPFS
            url = f"https://api.pinata.cloud/pinning/unpin/{file.cid}"
            headers = {
                'pinata_api_key': request.user.pinata_api_key,
                'pinata_secret_api_key': request.user.pinata_secret
            }
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 200:
                file.delete()
                messages.success(request, 'File removed successfully')
            else:
                messages.error(request, f'Error removing file from IPFS: {response.text}')
        except CaseFile.DoesNotExist:
            messages.error(request, 'File not found')
    
    share_form = ShareCaseForm()
    disclosure_form = DisclosureFormForm() if request.user.role == 'police' else None
    file_form = CaseFileForm()
    
    return render(request, 'case_mgmt/case_detail.html', {
        'case': case,
        'file_form': file_form,
        'share_form': share_form,
        'disclosure_form': disclosure_form,
        'activity_logs': case.activity_logs.order_by('-timestamp')[:10],
    })

@login_required
def my_cases_view(request):
    if request.user.role != 'forensic':
        messages.error(request, 'Only forensic users can view this page')
        return redirect('home')
    
    status_filter = request.GET.get('status', None)
    cases = Case.objects.filter(created_by=request.user)
    
    if status_filter:
        cases = cases.filter(status=status_filter)
    
    return render(request, 'case_mgmt/my_cases.html', {
        'cases': cases.order_by('-created_at'),
        'status_filter': status_filter,
    })

@login_required
def notifications_view(request):
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')
    return render(request, 'case_mgmt/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('case_detail', case_id=notification.case.id)

@login_required
def delete_case_view(request, case_id):
    if request.user.role != 'forensic':
        messages.error(request, 'Only forensic users can delete cases')
        return redirect('home')
    
    case = get_object_or_404(Case, id=case_id, created_by=request.user)
    
    if request.method == 'POST':
        # First unpin all files from IPFS
        for case_file in case.files.all():
            try:
                url = f"https://api.pinata.cloud/pinning/unpin/{case_file.cid}"
                headers = {
                    'pinata_api_key': request.user.pinata_api_key,
                    'pinata_secret_api_key': request.user.pinata_secret
                }
                requests.delete(url, headers=headers)
            except:
                pass
        
        case.delete()
        messages.success(request, 'Case deleted successfully')
        return redirect('my_cases')
    
    return render(request, 'case_mgmt/confirm_delete.html', {'case': case})

@login_required
def update_case_view(request, case_id):
    if request.user.role != 'forensic':
        messages.error(request, 'Only forensic users can update cases')
        return redirect('home')
    
    case = get_object_or_404(Case, id=case_id, created_by=request.user)
    
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            updated_case = form.save()
            
            # Log activity
            CaseActivityLog.objects.create(
                case=updated_case,
                user=request.user,
                activity=f"Case updated by {request.user.username}"
            )
            
            messages.success(request, 'Case updated successfully')
            return redirect('case_detail', case_id=updated_case.id)
    else:
        form = CaseForm(instance=case)
    
    return render(request, 'case_mgmt/update_case.html', {'form': form, 'case': case})

# AJAX view for file upload
@login_required
def upload_file_view(request, case_id):
    if request.method == 'POST' and request.FILES:
        case = get_object_or_404(Case, id=case_id)
        
        if not request.user.is_ipfs_connected:
            return JsonResponse({'error': 'Please connect to Pinata IPFS first'}, status=400)
        
        file = request.FILES['file']
        file_name = file.name
        file_type = file_name.split('.')[-1].lower()
        
        try:
            # Upload to Pinata IPFS
            url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
            headers = {
                'pinata_api_key': request.user.pinata_api_key,
                'pinata_secret_api_key': request.user.pinata_secret
            }
            files = {'file': file}
            response = requests.post(url, files=files, headers=headers)
            
            if response.status_code == 200:
                cid = response.json()['IpfsHash']
                case_file = CaseFile.objects.create(
                    case=case,
                    file_name=file_name,
                    cid=cid,
                    file_type=file_type
                )
                
                return JsonResponse({
                    'success': True,
                    'file_id': case_file.id,
                    'file_name': file_name,
                    'cid': cid,
                    'file_type': file_type,
                    'uploaded_at': case_file.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'view_url': f'https://gateway.pinata.cloud/ipfs/{cid}'
                })
            else:
                return JsonResponse({'error': response.text}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def add_disclosure_form(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST' and request.user.role == 'police':
        form = DisclosureFormForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Temporary save signature
                signature_file = request.FILES['signature_image']
                temp_signature_path = f"/tmp/{signature_file.name}"
                with open(temp_signature_path, 'wb+') as destination:
                    for chunk in signature_file.chunks():
                        destination.write(chunk)
                
                # Upload signature to IPFS
                signature_url = f"https://api.pinata.cloud/pinning/pinFileToIPFS"
                with open(temp_signature_path, 'rb') as sig_file:
                    signature_response = requests.post(
                        signature_url,
                        files={'file': sig_file},
                        headers={
                            'pinata_api_key': request.user.pinata_api_key,
                            'pinata_secret_api_key': request.user.pinata_secret
                        }
                    )
                os.remove(temp_signature_path)  # Clean up temp file
                
                if signature_response.status_code != 200:
                    raise Exception("Signature upload failed")
                
                signature_cid = signature_response.json()['IpfsHash']
                
                # Generate PDF with signature
                signature_url = f"https://gateway.pinata.cloud/ipfs/{signature_cid}"
                temp_pdf_path = "/tmp/disclosure_temp.pdf"
                pdf_content = build_pdf_content(case, request.user, signature_url)
                
                with open(temp_pdf_path, 'wb') as pdf_file:
                    pdf_file.write(pdf_content)
                
                # Upload PDF to IPFS
                with open(temp_pdf_path, 'rb') as pdf_file:
                    pdf_response = requests.post(
                        signature_url,
                        files={'file': pdf_file},
                        headers={
                            'pinata_api_key': request.user.pinata_api_key,
                            'pinata_secret_api_key': request.user.pinata_secret
                        }
                    )
                os.remove(temp_pdf_path)  # Clean up temp file
                
                if pdf_response.status_code != 200:
                    raise Exception("PDF upload failed")
                
                pdf_cid = pdf_response.json()['IpfsHash']
                
                # Save disclosure form
                disclosure = DisclosureForm.objects.create(
                    case=case,
                    added_by=request.user,
                    form_pdf_cid=pdf_cid,
                    signature_image_cid=signature_cid,
                    form_name=form.cleaned_data['form_name'],
                    remarks=form.cleaned_data['remarks']
                )
                
                # Notify court users
                court_users = CustomUser.objects.filter(role='court')
                for user in court_users:
                    Notification.objects.create(
                        user=user,
                        case=case,
                        message=f"New disclosure form added by {request.user.username}"
                    )
                
                case.disclosure_added = True
                case.disclosure_added_at = timezone.now()
                case.disclosure_added_by = request.user
                case.save()
                
                messages.success(request, 'Disclosure form added successfully!')
                return redirect('case_detail', case_id=case.id)
                
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = DisclosureFormForm()
    
    return render(request, 'case_mgmt/add_disclosure.html', {
        'form': form,
        'case': case
    })

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if user_form.is_valid():
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                try:
                    profile_file = request.FILES['profile_picture']
                    response = requests.post(
                        "https://api.pinata.cloud/pinning/pinFileToIPFS",
                        files={'file': profile_file},
                        headers={
                            'pinata_api_key': request.user.pinata_api_key,
                            'pinata_secret_api_key': request.user.pinata_secret
                        }
                    )
                    if response.status_code == 200:
                        request.user.profile_picture_cid = response.json()['IpfsHash']
                except Exception as e:
                    messages.error(request, f"Error uploading profile picture: {str(e)}")
            
            user_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=request.user)
    
    return render(request, 'case_mgmt/profile.html', {
        'user_form': user_form
    })