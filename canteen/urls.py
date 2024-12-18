from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from canteenapp import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    #admin
    path('admin/', admin.site.urls),
    path('',views.home,name='home'),
    path('userlogin/',views.index,name='index'),
    path('sendverificationcode/',views.sendverificationcode,name='sendverificationcode'),
    path('loginverification/',views.loginverification,name='loginverification'),
    path('signupverification/',views.signupverification,name='signupverification'),
    path('sendsignverificationcode/',views.sendsignverificationcode,name='sendsignverificationcode'),
    path('signupverifymail/',views.signupverifymail,name='signupverifymail'),
    path('loginverifymail/',views.loginverifymail,name='loginverifymail'),
    path('adminlogin/',views.adminlogin,name='adminlogin'),
    path('admintemplate/',views.admintemplate,name='admintemplate'),
    path('admindashboard/',views.admindashboard,name='admindashboard'),
    path('admindeliverypersonal/',views.admindeliverypersonal,name='admindeliverypersonal'),
    path('adminaddpersonnel/',views.adminaddpersonnel,name='adminaddpersonnel'),
    path('admingetdeliverypersonnels/',views.admin_get_delivery_personnels,name='admingetdeliverypersonnels'),
    path('deletedeliverypersonnel/',views.deletedeliverypersonnel,name='deletedeliverypersonnel'),
    path('updatedeliverypersonnel/',views.updatedeliverypersonnel,name='updatedeliverypersonnel'),
    path('adminmenu/',views.adminmenu,name='adminmenu'),
    path('adminaddmenu/',views.adminaddmenu,name='adminaddmenu'),
    path('admingetmenu/',views.admingetmenu,name='admingetmenu'),
    path('adminupdatemenu/',views.adminupdatemenu,name='adminupdatemenu'),
    path('admindeletemenu/',views.admindeletemenu,name='admindeletemenu'),
    path('adminsubmenu/',views.adminsubmenu,name='adminsubmenu'),
    path('adminaddsubmenu/',views.adminaddsubmenu,name='adminaddsubmenu'),
    path('admingetsubmenu/',views.admingetsubmenu,name='admingetsubmenu'),
    path('adminupdatesubmenu/',views.adminupdatesubmenu,name='adminupdatesubmenu'),
    path('admindeletesubmenu/',views.admindeletesubmenu,name='admindeletesubmenu'),
    path('adminitems/',views.adminitems,name='adminitems'),
    path('admingetsubmenusfordropdown/',views.admingetsubmenusfordropdown,name='admingetsubmenusfordropdown'),
    path('adminadditem/',views.adminadditem,name='adminadditem'),
    path('admingetallitems/',views.admingetallitems,name='admingetallitems'),
    path('admindeleteitem/',views.admindeleteitem,name='admindeleteitem'),
    path('adminupdateitem/',views.adminupdateitem,name='adminupdateitem'),
    path('adminupdateitemimage/',views.adminupdateitemimage,name='adminupdateitemimage'),
    path('adminpriceupdation/',views.adminpriceupdation,name='adminpriceupdation'),
    path('adminaddprice/',views.adminaddprice,name='adminaddprice'),
    path('admingetaddprices/',views.admingetaddprices,name='admingetaddprices'),
    path('updatedelivery_type/',views.updatedelivery_type,name='updatedelivery_type'),
    path('adminupdateprices/',views.adminupdateprices,name='adminupdateprices'),
    path('admindeleteprice/',views.admindeleteprice,name='admindeleteprice'),
    path('adminneworders/',views.adminneworders,name='adminneworders'),
    path('getneworder/',views.getneworder,name='getneworder'),
    path('adminconfirmorder/',views.adminconfirmorder,name='adminconfirmorder'),
    path('admincancelorder/',views.admincancelorder,name='admincancelorder'),
    path('adminallorders/',views.adminallorders,name='adminallorders'),
    path('admingetallorder/',views.admingetallorder,name='admingetallorder'),
    path('admindeliveredorders/',views.admindeliveredorders,name='admindeliveredorders'),
    path('admingetdeliveredorders/',views.admingetdeliveredorders,name='admingetdeliveredorders'),
    path('admincancelledorders/',views.admincancelledorders,name='admincancelledorders'),
    path('admingetcancelledorders/',views.admingetcancelledorders,name='admingetcancelledorders'),
    path('admindeliverylocations/',views.admindeliverylocations,name='admindeliverylocations'),
    path('adminaddlocation/',views.adminaddlocation,name='adminaddlocation'),
    path('admingetlocations/',views.admingetlocations,name='admingetlocations'),
    path('admindeletelocation/',views.admindeletelocation,name='admindeletelocation'),
    path('adminallusers/',views.adminallusers,name='adminallusers'),
    path('admingetallusers/',views.admingetallusers,name='admingetallusers'),
    path('admindeleteuser/',views.admindeleteuser,name='admindeleteuser'),
    path('admindeleteuser/',views.admindeleteuser,name='admindeleteuser'),
    path('admin_sales_overview/', views.admin_sales_overview, name='admin_sales_overview'),
    path('admin_top_selling_items/', views.admingettopsellingitems, name='admin_top_selling_items'),
    path('admin_order_breakdown/',views.admin_order_breakdown,name='admin_order_breakdown'),
    path('admin_order_counts/',views.admin_order_counts,name='admin_order_counts'),
    path('adminassignorder/',views.adminassignorder,name='adminassignorder'),
    path('admingettobeassignedorders/',views.admingettobeassignedorders,name='admingettobeassignedorders'),
    path('admingettobeassignedorders/',views.admingettobeassignedorders,name='admingettobeassignedorders'),
    path('adminassignordertodelivery/',views.adminassignordertodelivery,name='adminassignordertodelivery'),
    path('admindeliveryperformance/',views.admindeliveryperformance,name='admindeliveryperformance'),
    path('admin_get_delivery_personnels_performance/',views.admin_get_delivery_personnels_performance,name='admin_get_delivery_personnels_performance'),
    path('admin_get_delivery_personnel_performance_chart_data/',views.admin_get_delivery_personnel_performance_chart_data,name='admin_get_delivery_personnel_performance_chart_data'),
    path('admincustomerprofile/',views.admincustomerprofile,name='admincustomerprofile'),
    path('admingetcustomerorders/<str:email>/',views.admingetcustomerorders,name='admingetcustomerorders'),
    path('admingetorderdetails/<str:order_id>/',views.getorderdetails,name='getorderdetails'),
    path('adminorderhistory/',views.adminorderhistory,name='adminorderhistory'),
    path('adminsalesreports/',views.adminsalesreports,name='adminsalesreports'),
    path('admin_top_ordered_customers/',views.top_ordered_customers,name='admin_top_ordered_customers'),
    path('adminresturants/',views.adminresturants,name='adminresturants'),
    path('adminaddresturant/',views.adminaddresturant,name='adminaddresturant'),
    path('admingetresturant/',views.admingetresturant,name='admingetresturant'),
    path('adminupdateresturantimage/',views.adminupdateresturantimage,name='adminupdateresturantimage'),
    path('admindeleteresturant/',views.admindeleteresturant,name='admindeleteresturant'),

    #user
    path('getmenu/',views.getmenu,name='getmenu'),
    path('getallitems/',views.getallitems,name='getallitems'),
    path('checkout/',views.checkout,name='checkout'),
    path('getcartitems/',views.get_cart_items,name='get_cart_items'),
    path('updatecartitem/',views.update_cart_item,name='updatecartitem'),
    path('addtocart/',views.add_to_cart,name='addtocart'),
    path('profile/',views.profile,name='profile'),
    path('addphonenumber/',views.addphonenumber,name='addphonenumber'),
    path('updatemobilenumber/',views.updatemobilenumber,name='updatemobilenumber'),
    path('getorders/',views.getorders,name='getorders'),
    path('orderhistory/',views.orderhistory,name='orderhistory'),
    path('getorderdetails/<str:order_id>/',views.getorderdetails,name='getorderdetails'),
    path('filteritems/', views.filter_items, name='filter_items'),
    path('search/',views.search,name='search'),
    path('searchitems/', views.search_items, name='search_items'), 
    path('getlocations/',views.getlocations,name='getlocations'),
    path('user_logout_view/',views.user_logout_view,name='user_logout_view'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/', include('allauth.urls')),

    #delivery
    path('deliverylogin/',views.deliverylogin,name='deliverylogin'),
    path('deliverydashboard/',views.deliverydashboard,name='deliverydashboard'),
    path('deliveryneworders/',views.deliveryneworders,name='deliveryneworders'),
    path('deliverygetneworders/',views.deliverygetneworders,name='deliverygetneworders'),
    path('deliveryupdatetoshipped/',views.deliveryupdatetoshipped,name='deliveryupdatetoshipped'),
    path('deliveryupdatestatus/',views.deliveryupdatestatus,name='deliveryupdatestatus'),
    path('deliveryupdatedeliverystatus/',views.deliveryupdatedeliverystatus,name='deliveryupdatedeliverystatus'),
    path('deliverydelivered/',views.deliverydelivered,name='deliverydelivered'),
    path('deliverydeliveredorders/',views.deliverydeliveredorders,name='deliverydeliveredorders'),
    path('get_delivery_performance_chart_data/',views.get_delivery_performance_chart_data,name='get_delivery_performance_chart_data'),
    path('deliverytemplate/',views.deliverytemplate,name='deliverytemplate'),


    #app
    path('applogin/',views.applogin,name='applogin'),
    path('apphome/',views.apphome,name='apphome'),
    path('appsearch/',views.appsearch,name='appsearch'),
    path('appcheckout/',views.appcheckout,name='appcheckout'),
    path('appprofile/',views.appprofile,name='appprofile'),
    path('apporderhistory/',views.apporderhistory,name='apporderhistory'),
    path('apporderinfo/',views.apporderinfo,name='apporderinfo'),
    path('applogout/',views.applogout,name='applogout'),
    path('pagenotfound/',views.pagenotfound,name='pagenotfound'),
    path('initiate/', views.checkout_view, name='initiate_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failure/', views.payment_failure, name='payment_failure'),


    #resturant
    path('resturantdashoard/',views.resturantdashoard,name='resturantdashoard'),
    path('resturantitems/',views.resturantitems,name='resturantitems'),
    path('resturantlogin/',views.resturantlogin,name='resturantlogin'),
    path('restaurantgetmenu/',views.restaurantgetmenu,name='restaurantgetmenu'),
    path('restaurantgetsubmenusfordropdown/',views.restaurantgetsubmenusfordropdown,name='restaurantgetsubmenusfordropdown'),
    path('restaurantadditem/',views.restaurantadditem,name='restaurantadditem'),
    path('restaurantupdateitem/',views.restaurantupdateitem,name='restaurantupdateitem'),
    path('restaurantupdateitemimage/',views.restaurantupdateitemimage,name='restaurantupdateitemimage'),
    path('restaurantgetallitems/',views.restaurantgetallitems,name='restaurantgetallitems'),
    path('restaurantdeleteitem/',views.restaurantdeleteitem,name='restaurantdeleteitem'),
    path('restaurantallorders/',views.restaurantallorders,name='restaurantallorders'),
    path('restaurantgetallorder/',views.restaurantgetallorder,name='restaurantgetallorder'),
    path('restaruntcancelorder/',views.restaruntcancelorder,name='restaruntcancelorder'),
    path('restaurantneworders/',views.restaurantneworders,name='restaurantneworders'),
    path('restaurantgetneworder/',views.restaurantgetneworder,name='restaurantgetneworder'),
    path('restaurantdeliveredorders/',views.restaurantdeliveredorders,name='restaurantdeliveredorders'),
    path('restaurantgetdeliveredorders/',views.restaurantgetdeliveredorders,name='restaurantgetdeliveredorders'),
    path('restaurantcancelledorders/',views.restaurantcancelledorders,name='restaurantcancelledorders'),
    path('restaurantgetcancelledorders/',views.restaurantgetcancelledorders,name='restaurantgetcancelledorders'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
