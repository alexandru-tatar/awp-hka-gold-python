# Dokumentation: KI-Werkzeuge und Verweisdateien

*Status: Entwurf · Stand 24.11.2026 · Ticket HKA-83 · Verantwortlich: Yaraslau Krautsou*

Jedes neue App-Repository enthält die Regeln für KI-Assistenten schon beim Anlegen. Diese Seite sagt, wie das aufgebaut ist und wie das Team ein weiteres Werkzeug ergänzt. Sie gilt gleich für beide Golden Master (JavaScript und Python).

## Aufbau

| Datei | Zweck | Wer pflegt sie |
|---|---|---|
| [`AGENTS.md`](../AGENTS.md) | Der Einstieg für KI-Assistenten und die **einzige** Datei mit den Hinweisen: Skills lesen, verwaltete Dateien nicht ändern, Daten nur in `DATA_DIR`, am Ende `make check`. | Plattform (verwaltet) |
| [`AGENTS.local.md`](../AGENTS.local.md) | Eigene Hinweise des App-Teams. Die Datei ist optional und im Golden Master nicht vorhanden. `AGENTS.md` verweist darauf. | App-Team |
| [`CLAUDE.md`](../CLAUDE.md) | Verweisdatei für Claude Code. Sie enthält nur `@AGENTS.md` und keine eigenen Regeln. | Plattform (verwaltet) |
| [`.agents/skills/`](../.agents/skills/README.md) | Die Regeln selbst (sieben Skills). `AGENTS.md` verlangt, sie vor der ersten Änderung zu lesen. | Plattform (verwaltet) |

Die Regeln stehen an einer Stelle: in `AGENTS.md` und den Skills. Verweisdateien enthalten keine Regeln. Ändert sich eine Regel, ändert sich nur `AGENTS.md` oder ein Skill.

Warum so? Kein KI-Assistent liest `.agents/skills/` von selbst. Ohne Einstieg müsste jede Person ihrem Assistenten sagen, dass er die Regeln lesen soll. Das wissen Fachkräfte nicht.

## Welches Werkzeug liest was

Stand 24.11.2026. Die Angaben stammen aus der Dokumentation der Hersteller und ändern sich. Vor der Freigabe eines Werkzeugs prüfen.

| Werkzeug | Liest | Datei nötig |
|---|---|---|
| Claude Code | `CLAUDE.md`. `AGENTS.md` liest es nur, wenn es keine `CLAUDE.md` gibt. | `CLAUDE.md` (vorhanden) |
| Cursor, GitHub Copilot (VS Code), Codex, Windsurf | `AGENTS.md` direkt | keine |
| Andere Werkzeuge | je nach Werkzeug, siehe Dokumentation des Herstellers | im Zweifel eine Verweisdatei |

Welche Assistenten Fachkräfte an der HKA nutzen dürfen, ist noch offen (Datenschutz, Freigabe). Davon hängt ab, welche Verweisdateien das Team wirklich braucht.

## Ein weiteres Werkzeug ergänzen

1. Prüfen Sie in der Dokumentation des Werkzeugs, ob es `AGENTS.md` schon liest. Wenn ja, ist nichts zu tun.
2. Wenn nein: Legen Sie die Datei an, die das Werkzeug liest. Name und Ort stehen in seiner Dokumentation. Ein Beispiel ist `GEMINI.md`.
3. Die Datei enthält nur einen Verweis auf `AGENTS.md` und keine Regel. Verstehen die Werkzeuge `@AGENTS.md`, genügt diese Zeile. Sonst schreiben Sie einen Satz: „Lesen Sie zuerst die Datei `AGENTS.md` im Hauptordner und befolgen Sie sie.“
4. Setzen Sie vor den Verweis die Kopfzeile wie in `CLAUDE.md`: „Verwaltete Datei: nicht verändern (sonst PF-108).“
5. Tragen Sie die Datei in **beiden** Golden Mastern in diese Listen ein: `POINTERS` und `MANAGED` im Starter-Test (`tools/tests/starter/`) und in die Liste „Gleiche Pflichtdateien“ im selben Test. Ein Test stellt sicher, dass die Datei außer dem Verweis nichts enthält und in beiden Repositories gleich ist.
6. Ergänzen Sie die Zeile in der Tabelle oben und in der [Übersicht](uebersicht.md).
7. Führen Sie `make check` aus.

Schreiben Sie keine Regeln in die Verweisdatei. Eine Regel, die nur dort steht, gilt für die anderen Werkzeuge nicht.

## Prüfung

`make check-starter` prüft, dass `AGENTS.md` und `CLAUDE.md` vorhanden sind, dass `AGENTS.md` auf die Skills, `AGENTS.local.md` und `make check` verweist und dass jede Verweisdatei nur auf `AGENTS.md` verweist. Ob ein Assistent die Regeln dann einhält, prüft ein Testlauf mit einer neuen App und einem einfachen fachlichen Auftrag. Die automatische Prüfung der Regeln ist Teil von HKA-81.
