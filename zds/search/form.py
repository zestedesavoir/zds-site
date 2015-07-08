from django import forms
from haystack.forms import SearchForm

from zds.forum.models import Post, Topic
from zds.search.constant import MODEL_NAMES
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

        if MODEL_NAMES[0][0] not in self.cleaned_data["models"] and \
           MODEL_NAMES[1][0] not in self.cleaned_data["models"] and \
           MODEL_NAMES[2][0] not in self.cleaned_data["models"] and \
           MODEL_NAMES[3][0] not in self.cleaned_data["models"] and \
           MODEL_NAMES[4][0] not in self.cleaned_data["models"] and \
           MODEL_NAMES[5][0] not in self.cleaned_data["models"] and \
           MODEL_NAMES[6][0] not in self.cleaned_data["models"]:

            list_model_accepted = (Post, Topic, SearchIndexContent, SearchIndexContainer, SearchIndexExtract)

        else:

            if MODEL_NAMES[0][0] in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (Topic,)

            if MODEL_NAMES[1][0] in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (Post,)

            if MODEL_NAMES[6][0] in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (SearchIndexExtract,)

            if MODEL_NAMES[2][0] in self.cleaned_data["models"] or \
               MODEL_NAMES[3][0] in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (SearchIndexContent,)

                if MODEL_NAMES[2][0] in self.cleaned_data["models"]:
                    list_model_accepted = list_model_accepted + (SearchIndexExtract,)

            if MODEL_NAMES[2][0] not in self.cleaned_data["models"] and \
               MODEL_NAMES[3][0] in self.cleaned_data["models"]:
                sqs = sqs.exclude(type='article')

            if MODEL_NAMES[2][0] in self.cleaned_data["models"] and \
               MODEL_NAMES[3][0] not in self.cleaned_data["models"]:
                sqs = sqs.exclude(type='tutorial')

            if MODEL_NAMES[4][0] in self.cleaned_data["models"] or \
               MODEL_NAMES[5][0] in self.cleaned_data["models"]:
                list_model_accepted = list_model_accepted + (SearchIndexContainer,)

            if MODEL_NAMES[4][0] in self.cleaned_data["models"] and \
               MODEL_NAMES[5][0] not in self.cleaned_data["models"]:
                sqs = sqs.exclude(level='chapter')

            if MODEL_NAMES[4][0] not in self.cleaned_data["models"] and \
               MODEL_NAMES[5][0] in self.cleaned_data["models"]:
                sqs = sqs.exclude(level='part')

        return sqs.models(*list_model_accepted)
