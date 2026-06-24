# Integration Home Assistant - La Meteo Agricole

Cette integration personnalisee recupere les previsions publiques depuis `lameteoagricole.net` et expose une entite `weather`.

Elle lit la page de previsions a 10 jours configuree, puis suit automatiquement le lien vers la page heure par heure de la meme commune quand il est present.

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

## Entite Home Assistant

L'integration cree une entite de type `weather`.

Exemple :

```text
weather.la_meteo_agricole
```

Le nom exact peut varier selon ton installation. Pour le retrouver :

1. Aller dans **Outils de developpement > Etats**.
2. Chercher `weather.` ou `la_meteo_agricole`.
3. Remplacer `weather.la_meteo_agricole` par ton vrai nom d'entite dans les exemples ci-dessous.

## Donnees recuperees

### Etat courant

L'etat courant utilise la premiere prevision horaire disponible quand elle existe.

Champs exposes par l'entite `weather` :

- condition meteo ;
- temperature courante ;
- temperature ressentie ;
- humidite ;
- nebulosite ;
- vitesse du vent ;
- rafales ;
- direction du vent.

### Previsions quotidiennes

Les previsions quotidiennes contiennent :

- date ;
- condition meteo ;
- temperature maximale ;
- temperature minimale ;
- precipitation en mm ;
- probabilite de precipitation ;
- vitesse du vent ;
- rafales ;
- direction du vent.

### Previsions heure par heure

Les previsions heure par heure contiennent :

- date et heure ;
- condition meteo ;
- temperature ;
- temperature ressentie ;
- precipitation en mm ;
- probabilite de precipitation ;
- humidite ;
- nebulosite ;
- vitesse du vent ;
- rafales ;
- direction du vent.

### Ephemeride

Ces donnees sont exposees comme attributs de l'entite `weather`.

Soleil :

| Attribut | Description |
| --- | --- |
| `sunrise` | Heure de lever du soleil |
| `sunset` | Heure de coucher du soleil |
| `civil_twilight` | Plage complete du crepuscule civil |
| `civil_twilight_begin` | Debut du crepuscule civil |
| `civil_twilight_end` | Fin du crepuscule civil |
| `nautical_twilight` | Plage complete du crepuscule nautique |
| `nautical_twilight_begin` | Debut du crepuscule nautique |
| `nautical_twilight_end` | Fin du crepuscule nautique |
| `saint_of_day` | Saint du jour affiche dans l'ephemeride |

Lune :

| Attribut | Description |
| --- | --- |
| `moonrise` | Heure de lever de la lune |
| `moonset` | Heure de coucher de la lune |
| `moon_phase` | Phase lunaire actuelle |
| `moon_trend` | Tendance de la phase, par exemple croissante |
| `moon_age` | Age de la lune |
| `moon_illumination` | Illumination en pourcentage |
| `next_new_moon` | Prochaine nouvelle lune |
| `next_first_quarter` | Prochain premier quartier |
| `next_full_moon` | Prochaine pleine lune |
| `next_last_quarter` | Prochain dernier quartier |

## Exemples de cartes Home Assistant

Dans tous les exemples, remplace `weather.la_meteo_agricole` par le vrai nom de ton entite.

### Carte meteo native

```yaml
type: weather-forecast
entity: weather.la_meteo_agricole
forecast_type: daily
show_current: true
show_forecast: true
```

Pour afficher les previsions heure par heure :

```yaml
type: weather-forecast
entity: weather.la_meteo_agricole
forecast_type: hourly
show_current: true
show_forecast: true
```

### Carte Markdown pour l'ephemeride

```yaml
type: markdown
content: |
  ## Ephemeride

  **Lever du soleil :** {{ state_attr('weather.la_meteo_agricole', 'sunrise') }}

  **Coucher du soleil :** {{ state_attr('weather.la_meteo_agricole', 'sunset') }}

  **Crepuscule civil :** {{ state_attr('weather.la_meteo_agricole', 'civil_twilight') }}

  **Crepuscule nautique :** {{ state_attr('weather.la_meteo_agricole', 'nautical_twilight') }}

  **Saint du jour :** {{ state_attr('weather.la_meteo_agricole', 'saint_of_day') }}

  ## Lune

  **Lever de la lune :** {{ state_attr('weather.la_meteo_agricole', 'moonrise') }}

  **Coucher de la lune :** {{ state_attr('weather.la_meteo_agricole', 'moonset') }}

  **Phase :** {{ state_attr('weather.la_meteo_agricole', 'moon_phase') }}

  **Age :** {{ state_attr('weather.la_meteo_agricole', 'moon_age') }}

  **Illumination :** {{ state_attr('weather.la_meteo_agricole', 'moon_illumination') }} %
```

### Carte Markdown avec valeurs separees

```yaml
type: markdown
content: |
  ## Details ephemeride

  Lever : {{ state_attr('weather.la_meteo_agricole', 'sunrise') }}
  Coucher : {{ state_attr('weather.la_meteo_agricole', 'sunset') }}

  Civil : {{ state_attr('weather.la_meteo_agricole', 'civil_twilight_begin') }} - {{ state_attr('weather.la_meteo_agricole', 'civil_twilight_end') }}

  Nautique : {{ state_attr('weather.la_meteo_agricole', 'nautical_twilight_begin') }} - {{ state_attr('weather.la_meteo_agricole', 'nautical_twilight_end') }}
```

### Carte Markdown pour les prochaines phases lunaires

```yaml
type: markdown
content: |
  ## Prochaines phases lunaires

  Nouvelle lune : {{ state_attr('weather.la_meteo_agricole', 'next_new_moon') }}

  Premier quartier : {{ state_attr('weather.la_meteo_agricole', 'next_first_quarter') }}

  Pleine lune : {{ state_attr('weather.la_meteo_agricole', 'next_full_moon') }}

  Dernier quartier : {{ state_attr('weather.la_meteo_agricole', 'next_last_quarter') }}
```

### Carte Entities pour l'entite meteo

Cette carte affiche l'etat de l'entite. Les attributs detailles restent visibles en cliquant sur l'entite.

```yaml
type: entities
entities:
  - entity: weather.la_meteo_agricole
    name: La Meteo Agricole
```

## Tester les attributs

Dans **Outils de developpement > Modeles**, tu peux tester :

```jinja2
{{ state_attr('weather.la_meteo_agricole', 'sunrise') }}
{{ state_attr('weather.la_meteo_agricole', 'civil_twilight') }}
{{ state_attr('weather.la_meteo_agricole', 'saint_of_day') }}
{{ state_attr('weather.la_meteo_agricole', 'moon_phase') }}
{{ state_attr('weather.la_meteo_agricole', 'moon_illumination') }}
```

Pour voir tous les attributs exposes :

```jinja2
{{ states.weather.la_meteo_agricole.attributes }}
```

## Versionner et creer une archive

La version de l'integration est definie dans :

```text
custom_components/lameteoagricole/manifest.json
```

Exemple pour la version actuelle :

```json
"version": "0.3.0"
```

Pour generer les ZIP de distribution :

```powershell
python scripts\package.py
```

La commande cree les fichiers ZIP a partir de la version indiquee dans le manifest :

```text
dist/lameteoagricoleHA-v0.3.0.zip
dist/lameteoagricoleHA-latest.zip
```

Le dossier `dist/` est ignore par Git. L'idee est de versionner le code source dans GitHub, puis d'ajouter le ZIP versionne comme asset dans une release GitHub si tu veux distribuer une version precise.

## Workflow Git simple

Pour voir ce qui a change :

```powershell
git status
```

Pour enregistrer une modification localement :

```powershell
git add .
git commit -m "Description courte de la modification"
```

Pour envoyer les commits vers GitHub :

```powershell
git push
```

## Limites connues

Le site n'offre pas d'API publique documentee. Le parseur depend donc du HTML public et peut necessiter un ajustement si le site change sa structure.

Certaines donnees avancees du site peuvent etre reservees aux abonnes ou absentes selon la commune et la page chargee.
