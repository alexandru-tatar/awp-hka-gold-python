---
name: barrierefreiheit
description: Verwenden bei Seiten, Formularen, Tabellen, Farben, Bildern und Tastaturbedienung, und immer wenn „barrierefrei“ verlangt wird (WCAG 2.1 AA).
---

# Barrierefreiheit (WCAG 2.1 AA)

Barrierefreiheit ist Pflicht und kein Zusatz. Jede Person muss die App bedienen können: mit der Tastatur, mit einem Screenreader und bei schwacher Sehkraft.

## Regeln

| ID | Regel | Stufe |
|---|---|---|
| R-A11Y-1 | Text hat mindestens den Kontrast 4,5 : 1 (große Schrift 3 : 1). | muss |
| R-A11Y-2 | Alle Funktionen sind per Tastatur bedienbar; der Fokus ist immer sichtbar. | muss |
| R-A11Y-3 | Jedes Formularfeld hat eine sichtbare Beschriftung (`<label for>`); Fehlertexte sind mit dem Feld verknüpft. | muss |
| R-A11Y-4 | Tabellen haben `<caption>` und Spaltenköpfe mit `scope`. | muss |
| R-A11Y-5 | Überschriften folgen einer Ordnung ohne Sprünge (h1 → h2 → h3). | muss |
| R-A11Y-6 | Informationen werden nie nur durch Farbe vermittelt. | muss |
| R-A11Y-7 | Bilder haben einen Alternativtext (dekorative Bilder: leer). | muss |
| R-A11Y-8 | Texte sind in einfacher Sprache: kurze Sätze, keine unerklärten Fachwörter. | soll |

## So geht es im Python-Starter

1. **Kontrast:** Farben nur aus den Variablen des Portals (Skill `design`). Diese Paare sind geprüft. Eigene Farben machen den Kontrast kaputt.
2. **Tastatur:** Aktionen sind `<a>` oder `<button>`, nie `<div onclick=…>`. Schreiben Sie nie `outline: none`. Der Fokus bleibt immer sichtbar.
3. **Formulare:** Jedes Feld hat ein sichtbares `<label for>`. Hinweis und Fehlertext sind mit `aria-describedby` am Feld verknüpft. `aria-describedby` nennt nur IDs, die es gibt. `aria-invalid` steht nur im Fehlerfall. In der Jinja2-Vorlage setzen Sie beides mit `{% if %}` nur, wenn es einen Fehler gibt.
4. **Tabellen:** immer `<caption>`, Spaltenköpfe mit `scope="col"`, erste Zelle jeder Zeile als `<th scope="row">`.
5. **Überschriften:** Pro Seite genau eine `<h1>`. Danach `<h2>`, `<h3>` ohne Sprung.
6. **Bilder:** Jedes Bild hat `alt`. Ein dekoratives Bild hat `alt=""`. Ein Icon steht neben Text und trägt `aria-hidden="true" focusable="false"`.
7. **Farbe allein reicht nie:** Ein Fehler hat immer einen Text. Ein Status hat immer ein Wort.
8. **Sprache:** kurze Sätze (im Mittel höchstens 20 Wörter), keine Fachwörter ohne Erklärung.
9. **Zahlen:** Zahlen stehen deutsch mit Komma („2,3“, nicht „2.3“). Noten liefert das Notensystem schon als Text mit Komma. Eigene Zahlen schreibt Python sonst mit Punkt. Formatieren Sie sie vor der Ausgabe, zum Beispiel mit `f"{wert:.1f}".replace(".", ",")`.

Formularfeld mit Fehler (Jinja2-Vorlage):

```html
<div class="field">
  <label for="subject">Betreff <span class="field__required">(Pflichtfeld)</span></label>
  <p id="subject-hint" class="field__hint">Höchstens 120 Zeichen.</p>
  <input id="subject" name="subject" type="text" maxlength="120" value="{{ subject }}"
         aria-describedby="subject-hint{% if errors.subject %} subject-error{% endif %}"
         {% if errors.subject %}aria-invalid="true"{% endif %} required>
  {% if errors.subject %}
  <p id="subject-error" class="field__error">{{ errors.subject }}</p>
  {% endif %}
</div>
```

Datentabelle:

```html
<div class="table-wrap" role="region" aria-labelledby="grades-caption" tabindex="0">
  <table class="table">
    <caption id="grades-caption">Meine Noten</caption>
    <thead><tr><th scope="col">Modul</th><th scope="col" class="num">Note</th></tr></thead>
    <tbody>
      {% for g in grades %}
      <tr><th scope="row">{{ g.module }}</th><td class="num">{{ g.grade }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

## Gut / schlecht

| Schlecht | Gut |
|---|---|
| hellgraue Schrift `#9a9fa8` auf Weiß (2,66 : 1) | `color: var(--ink-muted);` für Hinweise |
| Menüpunkt als `<div onclick=…>` | `<a href=…>` oder `<button type="button">` |
| `<input placeholder="Betreff">` ohne `<label>` | `<label for="subject">Betreff</label>` und `<input id="subject">` |
| Tabelle nur aus `<td>` ohne Überschrift | `<caption>` und `<th scope="col">` |
| `<h1>` gefolgt von `<h4>` | `<h1>`, dann `<h2>`, dann `<h3>` |
| Fehlerfeld nur rot umrandet, kein Text | `<p class="field__error">Bitte geben Sie einen Betreff ein.</p>` |
| `aria-describedby="subject-error"`, aber das Element fehlt | die ID nur nennen, wenn der Fehlertext da ist (`{% if %}`) |
| `<img src="diagramm.png">` ohne `alt` | `<img src="diagramm.png" alt="Notenverlauf als Diagramm">` |
| Note als `2.3` | Note als `2,3` |
| „Die Persistenzschicht-Initialisierung ist fehlgeschlagen.“ | „Die Daten konnten nicht geladen werden.“ |

## Prüfungen, die das absichern

A = automatisch, H = halbautomatisch (eine Person bestätigt), M = manuell (eine Person prüft). Die Prüfstellen stehen in `.agents/skills/README.md`.

| ID | Prüfung |
|---|---|
| R-A11Y-1 | A (`ci`: Kontrastprüfung der Gestaltungswerte und Browser-Test) |
| R-A11Y-2 | A (`ci`: Tastatur-Durchlauf) |
| R-A11Y-3 | A (`test`) |
| R-A11Y-4 | A (`test`) |
| R-A11Y-5 | A (`test`) |
| R-A11Y-6 | M (`prf`) |
| R-A11Y-7 | A (`test`) |
| R-A11Y-8 | M (`prf`) |

Legen Sie für jede neue Seite einen Test in `tests/` an, der sie mit dem Test-Client aufruft. Sonst wird sie nicht geprüft. Ein Beispiel steht in `tests/test_app.py`.

## Vor dem Abschluss

- [ ] Nur Farben aus den Variablen des Portals
- [ ] Alles ist mit der Tastatur erreichbar, der Fokus ist sichtbar
- [ ] Jedes Feld hat ein Label; Fehler stehen als Text am Feld
- [ ] Tabellen haben `<caption>` und `scope`
- [ ] Eine `<h1>`, keine Sprünge in den Überschriften
- [ ] Jedes Bild hat `alt`
- [ ] Kein Hinweis nur durch Farbe
- [ ] Jede Seite wird in einem Test aufgerufen
- [ ] `make lint` und `make test` laufen ohne Fehler
