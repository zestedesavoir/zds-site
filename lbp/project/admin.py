from django.contrib import admin
from lbp.project.models import Plateform, Technology, Criteria, Evaluation, Note, Participation, CompetenceFonctionnelle, CompetenceTechno, Fonction, CompetencePlateforme, Project, ProjectFollowed, ProjectRead, BPlan
 

admin.site.register(BPlan)
admin.site.register(Plateform)
admin.site.register(Technology)
admin.site.register(Criteria)
admin.site.register(Evaluation)
admin.site.register(Note)
admin.site.register(Participation)
admin.site.register(CompetenceFonctionnelle)
admin.site.register(CompetenceTechno)
admin.site.register(Fonction)
admin.site.register(CompetencePlateforme)
admin.site.register(Project)
admin.site.register(ProjectRead)
admin.site.register(ProjectFollowed)