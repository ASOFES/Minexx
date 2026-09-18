class DatabaseRouter:
    """
    Routeur pour gérer la répartition des modèles entre les bases de données
    """
    
    # Liste des modèles qui doivent aller dans la base secondaire
    secondaire_models = {
        'rapport',  # Tous les modèles de l'app 'rapport'
        'notifications',  # Tous les modèles de l'app 'notifications'
        'core',  # Pour avoir accès au modèle Utilisateur
        'auth',  # Pour les permissions et groupes
        'contenttypes',  # Pour les types de contenu
        # 'securite',  # NE PAS METTRE ICI
    }
    
    # Liste des apps qui doivent être migrées en premier
    priority_apps = {
        'contenttypes',
        'auth',
        'admin',
        'sessions',
    }
    
    def db_for_read(self, model, **hints):
        """
        Suggère quelle base de données utiliser pour les opérations de lecture
        """
        if model._meta.app_label in self.secondaire_models:
            return 'secondaire'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Suggère quelle base de données utiliser pour les opérations d'écriture
        """
        if model._meta.app_label in self.secondaire_models:
            return 'secondaire'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Détermine si une relation entre deux objets est autorisée
        """
        # Autoriser toutes les relations
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Détermine si les migrations doivent être appliquées à une base de données
        """
        # Si c'est une app prioritaire, la migrer dans les deux bases
        if app_label in self.priority_apps:
            return True
            
        # Pour les autres apps, suivre la configuration secondaire_models
        if app_label in self.secondaire_models:
            return db == 'secondaire'
        return db == 'default' 