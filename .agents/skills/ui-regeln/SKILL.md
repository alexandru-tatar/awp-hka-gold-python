---
name: ui-regeln
description: Verwenden bei Dialogen, Knöpfen, Meldungen, Fehlertexten, Pflichtfeldern und Formularen, und immer wenn eine Aktion nicht rückgängig zu machen ist, zum Beispiel beim Senden einer Nachricht oder beim Löschen.
---

# UI-Regeln

Alle Apps im Portal fühlen sich gleich an. Menü, Dialoge, Knöpfe und Texte folgen festen Mustern. So finden sich die Menschen überall zurecht.

## Regeln

| ID | Regel | Stufe |
|---|---|---|
| R-UI-1 | Das Menü steht links und kommt vom Portal (`layout()`); die App baut kein eigenes. | muss |
| R-UI-2 | Ein Dialog hat genau zwei Knöpfe: „Abbrechen" und die Aktion. | muss |
| R-UI-3 | Knöpfe nennen die Aktion als Verb („Senden", „Speichern"), nicht „OK" oder „Ja". | muss |
| R-UI-4 | Pflichtfelder sind mit dem Text „Pflichtfeld" gekennzeichnet, nicht nur durch Farbe oder Stern. | soll |
| R-UI-5 | Fehlermeldungen sagen, was falsch ist und wie man es behebt. | soll |
| R-UI-6 | Vor nicht rückgängig zu machenden Aktionen fragt ein Dialog nach. | muss |
| R-UI-7 | Alle Texte für Nutzerinnen und Nutzer sind Deutsch, in einfacher Sprache und in der Sie-Form. | soll |

## So geht es im Python-Starter

1. **Menü:** Das Menü steht links und kommt von `portal.layout(...)`. Bauen Sie nie eine eigene `<nav>` mit Menüpunkten.
2. **Knöpfe:** Der Knopf nennt die Aktion als Verb: „Senden“, „Speichern“, „Abbrechen“. Nie „OK“, „Ja“ oder „Nein“. Pro Formular gibt es höchstens einen Knopf `btn--primary`.
3. **Dialog:** Er fragt vor einer Aktion, die sich nicht zurücknehmen lässt (zum Beispiel eine Nachricht senden). Er hat genau zwei Knöpfe: „Abbrechen“ links, die Aktion rechts. Der Titel ist eine Frage. Der Text nennt die Folge. Der Knopf, der den Dialog öffnet, endet mit „…“. Ein Dialog nur zur Information ist nicht erlaubt.
4. **Pflichtfelder:** Das Label trägt den Text „(Pflichtfeld)“ in `<span class="field__required">`. Ein Stern oder eine Farbe allein reicht nicht.
5. **Fehlermeldungen:** Sie sagen, was falsch ist und wie man es behebt. Bei mehreren Fehlern steht oben im Formular eine Zusammenfassung mit Links auf die Felder (`error-summary`).
6. **Eingaben prüfen:** Prüfen Sie Formulare in der Route selbst und zeigen Sie die Seite mit deutschen Fehlertexten erneut. Die automatische Antwort von FastAPI bei falschen Eingaben (Status 422, englischer JSON-Text) darf die Person nie sehen. Lesen Sie Formularfelder deshalb mit einem Ersatzwert, zum Beispiel `subject: str = Form("")`, und prüfen Sie danach selbst.
7. **Sprache:** Alle Texte sind Deutsch, in einfacher Sprache und in der Sie-Form. Das Portal setzt `lang="de"`. Verwenden Sie keine englischen Standardwörter wie „Submit“, „Cancel“ oder „Loading…“.

Formular selbst prüfen:

```python
@router.post("/send", response_class=HTMLResponse)
async def send(user: User = Depends(portal.user), subject: str = Form(""), text: str = Form("")):
    errors = {}
    if not subject.strip():
        errors["subject"] = "Bitte geben Sie einen Betreff ein."
    if errors:
        body = templates.get_template("form.html").render(errors=errors, subject=subject, text=text)
        return HTMLResponse(
            await portal.layout(title="Nachricht schreiben", body=body, current=portal.url("/"), user=user),
            status_code=400,
        )
    # …
```

Dialog mit genau zwei Knöpfen:

```html
<button type="button" class="btn btn--primary" data-dialog-open="confirm-send">Senden …</button>

<dialog id="confirm-send" aria-labelledby="confirm-send-title" data-submit-form="send-form">
  <form method="dialog">
    <h2 id="confirm-send-title">Nachricht senden?</h2>
    <p>Die Nachricht geht an das Studienbüro. Das lässt sich danach nicht zurücknehmen.</p>
    <div class="dialog__actions">
      <button value="cancel" class="btn btn--secondary">Abbrechen</button>
      <button value="confirm" class="btn btn--primary" autofocus>Senden</button>
    </div>
  </form>
</dialog>
```

`data-submit-form` nennt die ID des Formulars, das bei „Senden“ abgeschickt wird.

Fehlerzusammenfassung:

```html
{% if errors %}
<div class="error-summary" role="alert" tabindex="-1">
  <h2>Bitte prüfen Sie Ihre Eingaben</h2>
  <ul>
    {% for field, message in errors.items() %}
    <li><a href="#{{ field }}">{{ message }}</a></li>
    {% endfor %}
  </ul>
</div>
{% endif %}
```

## Gut / schlecht

| Schlecht | Gut |
|---|---|
| App enthält eine eigene `<nav>` mit Menüpunkten | Das Menü kommt vom Portal; die App liefert nur den Inhalt |
| Dialog mit „Ja“, „Nein“, „Vielleicht“ oder nur „OK“ | Zwei Knöpfe: „Abbrechen“ und „Senden“ |
| Knopf „OK“ | Knopf „Speichern“ |
| nur ein rotes `*` | „(Pflichtfeld)“ im Label |
| „Fehler 422“ oder `{"detail":[{"msg":"Field required"…}]}` | „Bitte geben Sie einen Betreff ein.“ |
| `subject: str = Form(...)` ohne eigene Prüfung | `subject: str = Form("")` und eigene Prüfung mit deutschem Text |
| Die Mail wird beim Klick auf „Senden“ sofort verschickt | Der Dialog „Nachricht senden?“ fragt vorher nach |
| Knopf „Submit“, Meldung „Loading…“ | Knopf „Senden“, Meldung „Die Daten werden geladen.“ |

## Prüfungen, die das absichern

A = automatisch, H = halbautomatisch (eine Person bestätigt), M = manuell (eine Person prüft). Die Prüfstellen stehen in `.agents/skills/README.md`.

| ID | Prüfung |
|---|---|
| R-UI-1 | A (`test`) |
| R-UI-2 | A (`test`) |
| R-UI-3 | A (`test`) |
| R-UI-4 | A (`test`) |
| R-UI-5 | M (`prf`) |
| R-UI-6 | M (`prf`) |
| R-UI-7 | M (`prf`; automatisch: `lang="de"`, keine englischen Standardwörter wie „Submit") |

## Vor dem Abschluss

- [ ] Keine eigene `<nav>`
- [ ] Jeder Dialog hat genau zwei Knöpfe, der Titel ist eine Frage
- [ ] Jeder Knopf nennt ein Verb; kein „OK“, kein „Ja“
- [ ] Pflichtfelder tragen den Text „(Pflichtfeld)“
- [ ] Jede Fehlermeldung sagt, was zu tun ist; keine englische 422-Antwort
- [ ] Vor jeder nicht umkehrbaren Aktion fragt ein Dialog nach
- [ ] Alle Texte sind Deutsch, einfach und in der Sie-Form
- [ ] `make lint` und `make test` laufen ohne Fehler
