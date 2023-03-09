from email import message
from unicodedata import category
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from ims_django.settings import MEDIA_ROOT, MEDIA_URL
import json
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db import IntegrityError
from imsApp.forms import SaveStock, UserRegistration, UpdateProfile, UpdatePasswords, SaveCategory, SaveStore ,SaveProduct, SaveInvoice, SaveInvoiceItem, StoreProductForm
from imsApp.models import Category, Product, Stock, Invoice, Invoice_Item,Store, StoreProduct
from cryptography.fernet import Fernet
from django.conf import settings
import base64
from .auth import admin_only

context = {
    'page_title' : 'File Management System',
}
#login
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
            else:
                resp['msg'] = "Incorrect username or password"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp),content_type='application/json')

#Logout
def logoutuser(request):
    logout(request)
    return redirect('/')

@login_required
def home(request):
    if request.user.is_superuser:
        context['page_title'] = 'Home'
        context['categories'] = Category.objects.count()
        context['products'] = Product.objects.count()
        context['sales'] = Invoice.objects.count()
        context['stores'] = Store.objects.count()
        context['users'] = User.objects.filter(is_superuser=0).count()
        return render(request, 'home.html',context)
    else:
        try:
            storeDetail = Store.objects.get(owner=request.user)
            context['page_title'] = 'Store Home'
            context['detail'] = storeDetail
            context['products'] = StoreProduct.objects.filter(store=storeDetail).count()
            context['sales'] = Invoice.objects.filter(store=storeDetail).count()
            context['unassigned'] = False
        except Store.DoesNotExist:
            context['page_title'] = 'User Home'
            context['unassigned'] = True
            return render(request,'unassigned.html',context)

        return render(request,'homeIndiv.html',context)

def registerUser(request):
    user = request.user
    if user.is_authenticated:
        return redirect('home-page')
    context['page_title'] = "Register User"
    if request.method == 'POST':
        data = request.POST
        form = UserRegistration(data)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            pwd = form.cleaned_data.get('password1')
            loginUser = authenticate(username= username, password = pwd)
            login(request, loginUser)
            return redirect('home-page')
        else:
            context['reg_form'] = form

    return render(request,'register.html',context)

@login_required
def update_profile(request):
    context['page_title'] = 'Update Profile'
    user = User.objects.get(id = request.user.id)
    if not request.method == 'POST':
        form = UpdateProfile(instance=user)
        context['form'] = form
        print(form)
    else:
        form = UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated")
            return redirect("profile")
        else:
            context['form'] = form
            
    return render(request, 'manage_profile.html',context)


@login_required
def update_password(request):
    context['page_title'] = "Update Password"
    if request.method == 'POST':
        form = UpdatePasswords(user = request.user, data= request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile")
        else:
            context['form'] = form
    else:
        form = UpdatePasswords(request.POST)
        context['form'] = form
    return render(request,'update_password.html',context)


@login_required
def profile(request):
    context['page_title'] = 'Profile'
    return render(request, 'profile.html',context)




# Category
@admin_only
@login_required
def category_mgt(request):
    context['page_title'] = "Product Categories"
    categories = Category.objects.all()
    context['categories'] = categories

    return render(request, 'category_mgt.html', context)

@admin_only
@login_required
def store_mgt(request):
    context['page_title'] = "Store"
    stores = Store.objects.all()
    context['stores'] = stores

    return render(request, 'store_mgt.html', context)


@login_required
def save_category(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            category = Category.objects.get(pk=request.POST['id'])
        else:
            category = None
        if category is None:
            form = SaveCategory(request.POST)
        else:
            form = SaveCategory(request.POST, instance= category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category has been saved successfully.')
            resp['status'] = 'success'
        else:
            print(form)
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type = 'application/json')



@login_required
def save_store(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            store = Store.objects.get(pk=request.POST['id'])
        else:
            store = None
        if store is None:
            form = SaveStore(request.POST)
        else:
            form = SaveStore(request.POST, instance= store)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store has been saved successfully.')
            resp['status'] = 'success'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type = 'application/json')


@login_required
def view_store(request,pk=None):
    if not pk is None:
        store = get_object_or_404(Store, pk=pk)
    else:
        store = get_object_or_404(Store,owner=request.user)
    store_products = store.storeproduct_set.all()

    return render(request, 'view_store.html', {'page_title':"View Prodcuts to Store",'store': store, 'store_products': store_products})


@admin_only
@login_required
def manage_category(request, pk=None):
    context['page_title'] = "Manage Category"
    if not pk is None:
        category = Category.objects.get(id = pk)
        context['category'] = category
    else:
        context['category'] = {}

    return render(request, 'manage_category.html', context)

@admin_only
@login_required
def manage_store(request, pk=None):
    context['page_title'] = "Manage store"
    context['category'] = Category.objects.all()
    context['users'] = User.objects.filter(is_superuser=0)
    if not pk is None:
        store = Store.objects.get(id = pk)
        context['store'] = store
    else:
        context['store'] = {}

    return render(request, 'manage_store.html', context)

@admin_only
@login_required
def manage_store_product(request,pk=None,pid=None):
    if pk is None:
        messages.error(request, "Store is not recognized")
        return redirect('store-detail')
    context['store'] = Store.objects.get(id=pk)
    context['products'] = Product.objects.all()
    # print('here')
    # print(pid)
    # print(pk)
    if pid:
        storeP = StoreProduct.objects.get(id = pid)
        store = storeP.store
        context['storeP'] = storeP
        context['store'] = store
        context['edit'] = True
    else:
        context['edit'] = False
        context['storeP'] = {}

    return render(request, 'manage_store_product.html', context)


@login_required
def delete_category(request):
    resp = {'status':'failed', 'msg':''}

    if request.method == 'POST':
        try:
            category = Category.objects.get(id = request.POST['id'])
            category.delete()
            messages.success(request, 'Category has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Category has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Category has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def delete_store(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        try:
            store = Store.objects.get(id = request.POST['id'])
            store.delete()
            messages.success(request, 'Store has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Store has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Store has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def delete_store_p(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        try:
            store_product = StoreProduct.objects.get(id = request.POST['id'])
            store_product.delete()
            messages.success(request, 'Store has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Store has failed to delete Product'
            print(err)

    else:
        resp['msg'] = 'Store has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")

# product
@admin_only
@login_required
def product_mgt(request):
    context['page_title'] = "Product List"
    products = Product.objects.all()
    context['products'] = products

    return render(request, 'product_mgt.html', context)

@login_required
def save_product(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            product = Product.objects.get(pk=request.POST['id'])
        else:
            product = None
        if product is None:
            form = SaveProduct(request.POST,request.FILES)
        else:
            form = SaveProduct(request.POST,request.FILES,instance= product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product has been saved successfully.')
            resp['status'] = 'success'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type = 'application/json')

@admin_only
@login_required
def manage_product(request, pk=None):
    context['page_title'] = "Manage Product"
    if not pk is None:
        product = Product.objects.get(id = pk)
        context['product'] = product
    else:
        context['product'] = {}

    return render(request, 'manage_product.html', context)

@login_required
def delete_product(request):
    resp = {'status':'failed', 'msg':''}

    if request.method == 'POST':
        try:
            product = Product.objects.get(id = request.POST['id'])
            product.delete()
            messages.success(request, 'Product has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Product has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Product has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")

#Inventory
# @admin_only
@login_required
def inventory(request,pk=None):
    context['page_title'] = 'Inventory'
    if request.user.is_superuser:
        products = Product.objects.all()
        context['products'] = products
    else:
        store = Store.objects.get(owner=request.user)
        products = StoreProduct.objects.filter(store=store)
        context['products'] = products
        context['isuser'] = True
        
    return render(request, 'inventory.html', context)

#Inventory History

@login_required
def inv_history(request, pk= None):
    context['page_title'] = 'Inventory History'
    if pk is None:
        messages.error(request, "Product ID is not recognized")
        return redirect('inventory-page')
    else:
        if request.user.is_superuser:
            product = Product.objects.get(id = pk)
            stocks = Stock.objects.filter(product = product).all()
            context['product'] = product
            context['stocks'] = stocks
        else:
            product = Product.objects.get(id = pk)
            store = Store.objects.get(owner=request.user)
            stocks = Stock.objects.filter(product = product,store=store ).all()
            context['product'] = product
            context['stocks'] = stocks
            context['isuser'] = True

        return render(request, 'inventory-history.html', context )

#Stock Form
@admin_only
@login_required
def manage_stock(request,pid = None ,pk = None):
    if pid is None:
        messages.error(request, "Product ID is not recognized")
        return redirect('inventory-page')
    context['pid'] = pid
    context['store'] = Store.objects.all()
    if pk is None:
        context['page_title'] = "Add New Stock"
        context['stock'] = {}
    else:
        context['page_title'] = "Manage New Stock"
        stock = Stock.objects.get(id = pk)
        context['stock'] = stock

    
    return render(request, 'manage_stock.html', context )


@login_required
def addProductStore(request, pk):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            store_p = StoreProduct.objects.get(pk=request.POST['id'])
        else:
            store_p = None
        if store_p is None:
            form = StoreProductForm(request.POST)
        else:
            form = StoreProductForm(request.POST, instance= store_p)
        if form.is_valid():
            # print(form.cleaned_data)
            try:
                detail = form.save(commit=False)
                detail.store = Store.objects.get(pk=pk)
                detail.stock = detail.count_inventory()
                detail.save()
                stock = Stock.objects.filter(product=request.POST['product']).first()
                
                messages.success(request, 'Product has been saved successfully.')
                resp['status'] = 'success'
            except IntegrityError as e:
                resp['msg'] = 'The Product already exists in the Store'
                    
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type = 'application/json')

@login_required
def save_stock(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            stock = Stock.objects.get(pk=request.POST['id'])
        else:
            stock = None
        if stock is None:
            form = SaveStock(request.POST)
        else:
            form = SaveStock(request.POST, instance= stock)
        if form.is_valid():
            # print(form.cleaned_data)
            try:
                storeP = StoreProduct.objects.get(product=request.POST['product'],store=request.POST['store'])
                storeP.stock = storeP.count_inventory()
                storeP.save()
                form.save()
                messages.success(request, 'Stock has been saved successfully.')
                resp['status'] = 'success'
            except StoreProduct.DoesNotExist:
                resp['msg'] = 'This product doesn\'t exist in the store. Please add it first.'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type = 'application/json')

@login_required
def delete_stock(request):
    resp = {'status':'failed', 'msg':''}

    if request.method == 'POST':
        try:
            stock = Stock.objects.get(id = request.POST['id'])
            stock.delete()
            messages.success(request, 'Stock has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Stock has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Stock has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")

@admin_only
@login_required
def sales_mgt(request):
    context['page_title'] = 'Sales'
    products = StoreProduct.objects.none()
    context['stores'] = Store.objects.all()
    context['products'] = products

    return render(request,'sales.html', context)


def get_store_products(request,sid=None):
    sid = request.GET.get('store')
    # store.storeproduct_set.all()
    store = Store.objects.get(pk=sid)
    store_products = StoreProduct.objects.filter(store=store)

    return render(request, 'storeP_dropdown.html', {'page_title':"View Prodcuts to Store",'store_products': store_products})



def get_product(request,pk = None):
    resp = {'status':'failed','data':{},'msg':''}
    if pk is None:
        resp['msg'] = 'Product ID is not recognized'
    else:
        product = Product.objects.get(id = pk)
        resp['data']['product'] = str(product.code + " - " + product.name)
        resp['data']['id'] = product.id
        resp['data']['price'] = product.price
        resp['status'] = 'success'
    
    return HttpResponse(json.dumps(resp),content_type="application/json")

def get_store_product(request,pk = None):
    resp = {'status':'failed','data':{},'msg':''}
    if pk is None:
        resp['msg'] = 'Product ID is not recognized'
    else:
        product = StoreProduct.objects.get(id = pk)
        resp['data']['product'] = str(product.product.code + " - " + product.__str__())
        resp['data']['id'] = product.id
        resp['data']['price'] = product.price
        resp['status'] = 'success'
    
    return HttpResponse(json.dumps(resp),content_type="application/json")

def save_sales(request):
    resp = {'status':'failed', 'msg' : ''}
    id = 2
    if request.method == 'POST':
        pids = request.POST.getlist('pid[]')
        print(pids)
        invoice_form = SaveInvoice(request.POST)
        if invoice_form.is_valid():
            invoice_form.save()
            invoice = Invoice.objects.last()
            for pid in pids:
                data = {
                    'invoice':invoice.id,
                    'storeproduct':pid,
                    'quantity':request.POST['quantity['+str(pid)+']'],
                    'price':request.POST['price['+str(pid)+']'],
                }
                print(data)
                ii_form = SaveInvoiceItem(data=data)
                # print(ii_form.data)
                if ii_form.is_valid():
                    ii_form.save()
                else:
                    for fields in ii_form:
                        for error in fields.errors:
                            resp['msg'] += str(error + "<br>")
                    break
            messages.success(request, "Sale Transaction has been saved.")
            resp['status'] = 'success'
            # invoice.delete()
        else:
            for fields in invoice_form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")

    return HttpResponse(json.dumps(resp),content_type="application/json")

@admin_only
@login_required
def invoices(request):
    invoice =  Invoice.objects.all()
    context['page_title'] = 'Invoices'
    context['invoices'] = invoice

    return render(request, 'invoices.html', context)

@login_required
def ownInvoice(request):
    store = Store.objects.get(owner=request.user)
    invoice = Invoice.objects.filter(store=store)
    context['page_title'] = store.name + " Invoices"
    context['invoices'] = invoice

    return render(request, 'invoices.html', context)

@login_required
def delete_invoice(request):
    resp = {'status':'failed', 'msg':''}

    if request.method == 'POST':
        try:
            invoice = Invoice.objects.get(id = request.POST['id'])
            invoice.delete()
            messages.success(request, 'Invoice has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Invoice has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Invoice has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")

@admin_only
@login_required
def stores():
    invoice =  Invoice.objects.all()
    context['page_title'] = 'Invoices'
    context['invoices'] = invoice

    return render(request, 'invoices.html', context)

