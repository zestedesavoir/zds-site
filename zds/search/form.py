from django import forms
from haystack.forms import SearchForm

from zds.forum.models import Post, Topic
from zds.search.constant import MODEL_NAMES, model_topic, model_post, model_extract, model_article, model_tutorial, \
    model_part, model_chapter
from zds.search.models import SearchIndexContent, SearchIndexContainer, SearchIndexExtract


class CustomSearchForm(SearchForm):

    models = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=False)

    def __init__(self, *args, **kwargs):
        super(CustomSearchForm, self).__init__(*args, **kwargs)

        self.fields['models'].choices = MODEL_NAMES

    def search(self):
        sqs = super(CustomSearchForm, self).search()

        if not self.is_valid():
            return self.no_query_found()

        list_model_accepted = ()

        if all([model[0] not in self.cleaned_data["models"] for model in MODEL_NAMES]):
            list_model_accepted = (Post, Topic, SearchIndexContent, SearchIndexContainer, SearchIndexExtract)

        else:
            if model_topic() in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (Topic,)

            if model_post() in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (Post,)

            if model_extract() in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (SearchIndexExtract,)

            if model_article() in self.cleaned_data["models"] or \
               model_tutorial() in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (SearchIndexContent,)

                if model_article() in self.cleaned_data["models"]:
                    list_model_accepted = list_model_accepted + (SearchIndexExtract,)

            if model_article() not in self.cleaned_data["models"] and \
               model_tutorial() in self.cleaned_data["models"]:
                sqs = sqs.exclude(type='article')

            if model_article() in self.cleaned_data["models"] and \
               model_tutorial() not in self.cleaned_data["models"]:
                sqs = sqs.exclude(type='tutorial')

            if model_part() in self.cleaned_data["models"] or \
               model_chapter() in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (SearchIndexContainer,)

            if model_part() in self.cleaned_data["models"] and \
               model_chapter() not in self.cleaned_data["models"]:
                sqs = sqs.exclude(level='chapter')

            if model_part() not in self.cleaned_data["models"] and \
               model_chapter() in self.cleaned_data["models"]:
                sqs = sqs.exclude(level='part')

        return sqs.models(*list_model_accepted)
