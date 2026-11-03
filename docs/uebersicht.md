# Dokumentation: Übersicht

*Status: Entwurf · Stand 01.11.2026 · Ticket HKA-22 · Verantwortlich: David Coric*

Golden Master für Portal-Apps: Python (FastAPI). Diese Seite zeigt, was wo liegt. Das Schwester-Repository `awp-hka-gold-js` hat dieselbe Struktur.

**Hinweis:** Der Starter liegt noch auf dem Branch `feat/golden-master-python`. Die Verweise auf das README und die Skills greifen erst nach dessen Merge.

## Was wo liegt

| Ort | Inhalt |
|---|---|
| [`README.md`](../README.md) | Befehle, Aufbau, Wartung, Selbsttests des Starters |
| [`.agents/skills/README.md`](../.agents/skills/README.md) | Regeln für die KI |
| [`betrieb/betriebsanleitung.md`](betrieb/betriebsanleitung.md) | Betriebsanleitung: Start, Stopp, Neustart, Fehlerfall, Aktualisieren, Zurücksetzen, Beenden, Sichern |
| [`adr/index.md`](adr/index.md) | Index der Architekturentscheidungen, Verweis auf Confluence |
| [`adr/0000-vorlage.md`](adr/0000-vorlage.md) | Vorlage für eine neue Entscheidung |

## Architektur

Der Starter hat keine eigenen Diagramme. Das C4-Diagramm liegt im Portal-Repository: [`docs/08-c4-container.md`](https://github.com/alexandru-tatar/awp-hka-intranet-portal/blob/main/docs/08-c4-container.md).

## Reservierte Pfade

Diese Pfade erzeugt später die Plattform. Legen Sie dort nichts von Hand an:

- `docs/schnittstellen/*.md`
- `docs/fehlercodes.md`
