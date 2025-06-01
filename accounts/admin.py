from django.contrib import admin
from .models import StateHeaderAll, DistrictHeaderAll, TalukaHeaderAll, VillageHeaderAll, ProjectLocationDetailsAll, Department, Project, Profile_header_all, User_header_all

admin.site.register(StateHeaderAll)
admin.site.register(DistrictHeaderAll)
admin.site.register(TalukaHeaderAll)
admin.site.register(VillageHeaderAll)
admin.site.register(ProjectLocationDetailsAll)
admin.site.register(Department)
admin.site.register(Project)
admin.site.register(Profile_header_all)
admin.site.register(User_header_all)
