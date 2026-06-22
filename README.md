# Integration Home Assistant - La Meteo Agricole

Cette integration personnalisee recupere les previsions publiques depuis `lameteoagricole.net` et expose une entite `weather`.

## Installation

1. Copier le dossier `custom_components/lameteoagricole` dans le dossier `custom_components` de Home Assistant.
2. Redemarrer Home Assistant.
3. Aller dans **Parametres > Appareils et services > Ajouter une integration**.
4. Chercher **La Meteo Agricole**.
5. Renseigner l'URL :

```text
https://www.lameteoagricole.net/previsions-meteo-agricole/Fains-la-Folie-28150.html
```

On peut aussi saisir seulement le code postal/recherche utilise par l'ancien endpoint :

```text
28150
```

## Donnees exposees

- condition meteo du jour ;
- temperature courante issue de la premiere prevision horaire disponible ;
- temperature maximale et minimale ;
- prevision quotidienne ;
- prevision heure par heure ;
- temperature ressentie heure par heure ;
- precipitation en millimetres ;
- probabilite de precipitation ;
- direction, vitesse et rafales de vent ;
- humidite et nebulosite heure par heure.

## Limites connues

L'integration recupere la page quotidienne configuree, puis suit automatiquement le lien `/meteo-heure-par-heure/...` de la meme commune quand il est present.

Le site n'offre pas d'API publique documentee ; le parseur depend donc du HTML public et peut necessiter un ajustement si le site change sa structure.
