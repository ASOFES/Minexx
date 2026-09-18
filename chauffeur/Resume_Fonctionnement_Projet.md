# Résumé global du fonctionnement du projet

## 1. Vue d'ensemble

Ce projet est une plateforme de gestion de flotte de véhicules, optimisée pour :
- La gestion des demandes de véhicules
- L'affectation et le suivi des chauffeurs
- Le dispatching des courses
- L'entretien et le ravitaillement
- La sécurité et la traçabilité des opérations

Chaque module correspond à un rôle ou à une fonction clé dans la chaîne de gestion.

---

## 2. Les modules et leurs rôles

### A. Demandeur
- **Rôle** : Utilisateur qui a besoin d'un véhicule pour une mission ou un déplacement.
- **Fonctionnalités** :
  - Soumettre une demande de véhicule (date, heure, destination, motif…)
  - Suivre l'état de sa demande (en attente, validée, refusée, en cours, terminée)
  - Recevoir des notifications sur l'évolution de la demande

### B. Dispatch
- **Rôle** : Responsable de la planification et de l'affectation des véhicules et chauffeurs.
- **Fonctionnalités** :
  - Visualiser toutes les demandes en attente
  - Affecter un véhicule et un chauffeur à chaque demande validée
  - Gérer le planning des courses
  - Suivre l'état des véhicules et la disponibilité des chauffeurs
  - Modifier ou annuler des affectations si besoin

### C. Chauffeur
- **Rôle** : Conducteur affecté à une course.
- **Fonctionnalités** :
  - Consulter ses missions/courses affectées
  - Accéder aux détails de la mission (demandeur, destination, horaires…)
  - Effectuer les check-lists de sécurité avant et après la course
  - Signaler tout incident ou problème rencontré pendant la mission
  - Saisir le kilométrage et l'état du véhicule au départ et au retour

### D. Administrateur Entretien
- **Rôle** : Responsable de la maintenance et de l'entretien des véhicules.
- **Fonctionnalités** :
  - Recevoir les alertes d'anomalies ou d'incidents signalés par les chauffeurs ou via les check-lists
  - Planifier et enregistrer les opérations d'entretien (vidange, révision, réparations…)
  - Suivre l'historique d'entretien de chaque véhicule
  - Gérer les indisponibilités des véhicules pour maintenance

### E. Ravitaillement
- **Rôle** : Gestionnaire du carburant et des consommables.
- **Fonctionnalités** :
  - Enregistrer les opérations de ravitaillement (carburant, huile, etc.)
  - Suivre la consommation de chaque véhicule
  - Générer des rapports de consommation
  - Détecter les anomalies de consommation (surconsommation, incohérences…)

### F. Administrateur (Superadmin)
- **Rôle** : Gestion globale de la plateforme.
- **Fonctionnalités** :
  - Gérer les utilisateurs et les rôles
  - Accéder à tous les modules et rapports
  - Configurer les paramètres du système
  - Superviser l'ensemble des opérations

---

## 3. Flux de travail typique

1. **Demande de véhicule**
   - Un demandeur soumet une demande via le module dédié.
   - Le dispatch reçoit la demande, la valide, puis affecte un véhicule et un chauffeur.

2. **Préparation de la course**
   - Le chauffeur reçoit la mission, effectue la check-list de sécurité « avant course ».
   - Si tout est conforme, il prend le véhicule ; sinon, il signale les anomalies.

3. **Réalisation de la mission**
   - Le chauffeur effectue la course.
   - En cas d'incident, il le signale via l'application.

4. **Retour et clôture**
   - Le chauffeur effectue la check-list « après course », saisit le kilométrage et l'état du véhicule.
   - Les éventuelles anomalies sont transmises à l'administrateur entretien.

5. **Entretien et ravitaillement**
   - L'administrateur entretien planifie les interventions nécessaires.
   - Le gestionnaire ravitaillement enregistre les pleins et suit la consommation.

6. **Supervision et reporting**
   - L'administrateur supervise l'ensemble, génère des rapports, et ajuste les paramètres si besoin.

---

## 4. Interactions et automatisations

- **Notifications** : Les utilisateurs reçoivent des notifications à chaque étape clé (validation, affectation, incident, etc.).
- **Automatisation des check-lists** : Le type de check-list (avant/après) est déterminé automatiquement selon le nombre de courses.
- **Validation des données** : Contrôle automatique du kilométrage, des statuts, et des anomalies.
- **Rapports** : Exports Excel/PDF pour toutes les opérations (demandes, entretiens, ravitaillements, check-lists…).

---

## 5. Sécurité et traçabilité

- **Historique complet** de toutes les actions (qui a fait quoi, quand, sur quel véhicule).
- **Contrôle d'accès** par rôle.
- **Sauvegarde automatique** des données.

---

## 6. Points forts du projet

- **Centralisation** de toute la gestion de flotte sur une seule plateforme.
- **Automatisation** des tâches répétitives et des validations.
- **Traçabilité** et reporting avancé.
- **Sécurité** des opérations et des données.

---

## 7. Exemple de scénario utilisateur

1. **Demandeur** : « Je fais une demande pour un véhicule demain à 8h. »
2. **Dispatch** : « Je valide la demande, j'affecte le véhicule 12 et le chauffeur Paul. »
3. **Chauffeur** : « Je fais la check-list avant, je pars en mission, je reviens, je fais la check-list après, je signale un pneu usé. »
4. **Entretien** : « Je planifie le changement de pneu. »
5. **Ravitaillement** : « J'enregistre le plein effectué au retour. »
6. **Administrateur** : « Je consulte les rapports et l'historique. »

---

## 8. Conclusion

Ce projet permet une gestion fluide, sécurisée et automatisée de toute la chaîne de mobilité : de la demande initiale à l'entretien, en passant par le suivi des chauffeurs, des véhicules, et des consommations.

---

**Pour toute question ou besoin de documentation détaillée par module, contactez l'administrateur du système.** 