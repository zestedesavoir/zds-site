from django.http.request import HttpRequest
from zds.gallery.models import Gallery, UserGallery, GALLERY_WRITE
from zds.tutorialv2.models.database import PublishableContent


def _get_content_gallery(content_pk, user):
    content = PublishableContent.objects.filter(pk=content_pk).first()
    if not content or user not in [content.authors.all()]:
        return {}
    content_gallery = content.gallery
    if not content_gallery:
        content.gallery = Gallery(title=content.title, subtitle=content.description, slug=content.slug)
        content.gallery.save()
        content_gallery = content.gallery
        for author in content.authors.all():
            UserGallery(user=author, gallery=content.gallery, mode=GALLERY_WRITE).save()
    return {'auto_update_gallery': content_gallery}


def _get_default_gallery(user):
    if not user or not user.is_authenticated():
        return {}

    user_default_gallery = UserGallery.objects.filter(user=user, is_default=True).first()
    if not user_default_gallery:
        gallery = Gallery(title='Gallerie par défaut', subtitle='', slug='gallerie-default')
        gallery.save()
        UserGallery(user=user, is_default=True, gallery=gallery, mode=GALLERY_WRITE).save()
    else:
        gallery = user_default_gallery.gallery
    return {'auto_update_gallery': gallery}


def get_auto_upload_gallery(request: HttpRequest):
    is_url_of_content = request.resolver_match and request.resolver_match.namespace == 'content'
    if request.user.is_authenticated() and is_url_of_content and 'pk' in request.resolver_match:
        return _get_content_gallery(request.resolver_match.kwargs['pk'], request.user)
    return _get_default_gallery(request.user)
