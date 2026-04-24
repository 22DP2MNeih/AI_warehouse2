from rest_framework import permissions

# PIEKĻUVES TIESĪBU PĀRVALDĪBA
# Šīs klases nosaka, kuras sistēmas daļas ir pieejamas dažādām lietotāju lomām.
# Piemēram, mehāniķiem var būt tikai lasīšanas tiesības vai piekļuve vienai noliktavai.
class IsAdminOrManagerOrReadOnly(permissions.BasePermission):
    """
    Pielāgota atļauja, kas ļauj labot/dzēst tikai administratoriem un noliktavas vadītājiem.
    Citi lietotāji var tikai lasīt (skatīt).
    """
    def has_permission(self, request, view):
        # Atļaut lasīšanas metodes visiem autentificētiem lietotājiem
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Rakstīšanas tiesības tikai Admin un Vadītājiem
        return request.user and (
            request.user.role in ['ADMIN', 'WAREHOUSE_MANAGER'] or request.user.is_superuser
        )

# Pārbauda, vai lietotājam ir mehāniķa loma.
class IsMechanic(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'MECHANIC'
