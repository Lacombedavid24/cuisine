from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import RecetteForm,EtapeFormset,RegistrationForm,IngredientFormset,ImageFormset, CommentaireForm, NoteForm, EtapeCustomForm
from .models import Ingredient,  Etape,  Photo,  Recette, Note, Commentaire, Type
from django import template
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pprint
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from django.db.models import Avg
from recette.views import Recette
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_list_or_404, get_object_or_404
from django.forms.models import modelformset_factory

TYPE_CHOICES = ['1','2','3','4'];

def index(request):

    recettes = Recette.objects.all().order_by('-id');
    typeObjet=None
    if request.method == 'GET':
        if request.GET.get('type'):
            if request.GET['type'] in TYPE_CHOICES:
                type = request.GET['type']
                typeObjet = Type.objects.get(id=type)
                recettes = Recette.objects.filter(type=type);
    paginator = Paginator(recettes, 10)
    page = request.GET.get('page')
    try:
        recettes = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        recettes = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        recettes = paginator.page(paginator.num_pages)
    contexte = {
        'typeObjet': typeObjet,
        'recettes': recettes,
    }
    return render(request, 'recette/index.html', contexte)


def register(request):
    if (request.method == 'POST'):
        user_form = RegistrationForm(request.POST)
        if user_form.is_valid():
            user = User.objects.create_user(request.POST['username'],request.POST['email'],request.POST['password1'])
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.save()
            contexte = {
                'form': AuthenticationForm,
                'success_message':'success'
            }
            return render(request, 'registration/login.html', contexte)
    else:
        user_form = RegistrationForm()
    contexte = {
        'formulaire': user_form,
    }
    return render(request, 'registration/register.html', contexte)


def recette(request, id):

    if (request.method == 'POST'):
        note_form = NoteForm(request.POST)
        commentaire_form = CommentaireForm(request.POST)

        if note_form.is_valid():
            note = note_form.save()
            note.recette = Recette.objects.get(id=id)
            note.user = request.user
            note.save()

        if commentaire_form.is_valid():
            commentaire = commentaire_form.save()
            commentaire.recette = Recette.objects.get(id=id)
            commentaire.user = request.user
            commentaire.save()

    recette = Recette.objects.get(id=id)
    etapes = Etape.objects.filter(recette=id)
    ingredients = Ingredient.objects.filter(recette=id)
    photos = Photo.objects.filter(recette=id)
    note = Note.objects.filter(recette=id).aggregate(Avg('note'))
    noted = 0
    if(request.user.is_authenticated()):
        noted = Note.objects.filter(recette=id,user=request.user).count()
    form_note = ''
    if noted == 0:
        form_note = NoteForm();
    commentaires = Commentaire.objects.filter(recette=id)
    form_com = CommentaireForm();
    contexte = {
        'recette'    : recette,
        'etapes'     : etapes,
        'ingredients': ingredients,
        'photos'     : photos,
        'note'     : note,
        'commentaires'     : commentaires,
        'form_note': form_note,
        'form_com': form_com,
    }
    return render(request, 'recette/affiche-recette.html', contexte)

def nouvelleRecette(request):

    form = RecetteForm()
    IngredientForm = IngredientFormset()
    EtapeForm = EtapeFormset()
    ImageForm = ImageFormset()

    if request.method == 'POST':
        form = RecetteForm(request.POST)
        if form.is_valid():
            recette = form.save()
            recette.user = request.user
            recette.save()
            IngredientForm = IngredientFormset(request.POST,instance=recette)
            if IngredientForm.is_valid():
                IngredientForm.save()
                EtapeForm = EtapeFormset(request.POST,instance=recette)
                if EtapeForm.is_valid():
                    EtapeForm.save()
                    ImageForm = ImageFormset(request.POST,request.FILES,instance=recette)
                    if ImageForm.is_valid():
                        ImageForm.save()
                        return render(request, "recette/nouvelle-recette.html", {
                            'form': form,
                            'IngredientForm': IngredientForm,
                            'EtapeForm': EtapeForm,
                            'ImageForm': ImageForm,
                            'success_message':'success'
                        })

    return render(request, "recette/nouvelle-recette.html", {
        'form': form,
        'IngredientForm': IngredientForm,
        'EtapeForm': EtapeForm,
        'ImageForm':ImageForm,
    })


def modifyRecette(request, id):
    recette = get_object_or_404(Recette, id=id)

    ingredientFormSetCustom = modelformset_factory(Ingredient)
    etapeFormSetCustom = modelformset_factory(Etape, form=EtapeCustomForm)
    photoFormSetCustom = modelformset_factory(Photo)

    ingredients = Ingredient.objects.filter(recette=recette)
    etapes = Etape.objects.filter(recette=recette)
    photos = Photo.objects.filter(recette=recette)

    IngredientForm = ingredientFormSetCustom(queryset=ingredients)
    EtapeForm = etapeFormSetCustom(queryset=etapes)
    ImageForm = photoFormSetCustom(queryset=photos)
    formRecette = RecetteForm(instance=recette)

    if request.method == 'POST':
        form = RecetteForm(request.POST)
        if form.is_valid():
            recette.type_id = form.cleaned_data['type']
            recette.titre = form.cleaned_data['titre']
            recette.cout = form.cleaned_data['cout']
            recette.difficulte = form.cleaned_data['difficulte']
            recette.temps_preparation = form.cleaned_data['temps_preparation']
            recette.temps_cuisson = form.cleaned_data['temps_cuisson']
            recette.temps_repos = form.cleaned_data['temps_repos']
            recette.user = request.user
            recette.save()

            results = Recette.objects.filter(user_id=request.user.id)
            contexte = {
                'results': results,
                'success_message':'success'
            }
            return render(request, 'recette/mes_recettes.html', contexte)

    return render(request, "recette/modify-recette.html", {
        'recette': recette,
        'form': formRecette,
        'IngredientForm': IngredientForm,
        'EtapeForm': EtapeForm,
        'ImageForm':ImageForm,
    })


def supprimerRecette(request, id):
    Recette.objects.get(id=id).delete()
    results = Recette.objects.filter(user_id=request.user.id)
    contexte = {
        'results': results
    }
    return render(request, 'recette/mes_recettes.html', contexte)

def search(request):

    query = request.GET.get('search_query')
    orderby = ''
    orderway = ''
    if request.GET.get('orderby') and request.GET.get('orderway'):
        orderby = request.GET.get('orderby')
        orderway = request.GET.get('orderway')
        if orderway == 'desc':
            results = Recette.objects.filter(titre__contains=query).order_by('-' + orderby).select_related()
        elif orderway == 'asc':
            results = Recette.objects.filter(titre__contains=query).order_by(orderby).select_related()
    else :
        results = Recette.objects.filter(titre__contains=query).select_related()

    paginator = Paginator(results, 10)
    page = request.GET.get('page')
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        results = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        results = paginator.page(paginator.num_pages)
    contexte = {
        'page': page,
        'orderby': orderby,
        'orderway': orderway,
        'query': query,
        'results' : results
    }
    return render(request, 'search/search_result.html', contexte)

def mes_recettes(request):
    results = None;
    if request.user.is_authenticated():
        results = Recette.objects.filter(user_id=request.user.id)
    contexte = {
        'results': results
    }
    return render(request, 'recette/mes_recettes.html', contexte)