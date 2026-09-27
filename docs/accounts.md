# Accounts en koppelingen

Alles werkt ook zonder deze accounts, in simulatie. Per dienst zet je de schakelaar in `.env`
op `false` zodra het account klaarstaat. Sleutels komen **alleen** in `.env`, nooit in git of in de chat.

| Dienst | Voor | Status | Nodig in `.env` |
|---|---|---|---|
| WhatsApp Cloud API (Meta) | US-1, US-2, US-4 | ✅ Werkt (testnummer) | `WHATSAPP_*` |
| Anthropic API | US-3 | Sleutel aanwezig, nog invullen | `ANTHROPIC_API_KEY` |
| ngrok | Webhooks (US-1, inkomende WhatsApp) | Nog regelen | `PUBLIEK_ADRES` |
| Twilio | US-1 | Nog regelen | `TWILIO_*` |
| Google Agenda | US-4 | Nog regelen | `GOOGLE_*` |

## WhatsApp Cloud API (Meta)

1. developers.facebook.com → My Apps → Create App → gebruiksdoel *Connect with customers through WhatsApp*.
2. Business portfolio aanmaken (`OMNIA`).
3. Use cases → WhatsApp → *Step 1. Try it out* (Step 2 en 3 zijn voor de demo niet nodig).
4. Noteer *Phone number ID* en *WhatsApp Business Account ID*.
5. Bij *To* → *Manage phone number list*: nummers van eigenaar en tweede demotelefoon toevoegen (max. 5).
6. Permanent token: https://business.facebook.com/settings/system-users → Add (`omnia-server`, Admin)
   → Assign assets (app + WhatsApp-account, Full control) → Generate new token
   (verloopt: Never; rechten `whatsapp_business_messaging`, `whatsapp_business_management`).
7. App secret: developers.facebook.com → app → App settings → Basic.
8. Sjabloon `omnia_gemiste_oproep` (Utility, Dutch) met `{{1}}` = bedrijfsnaam, voor US-1.

Test: `.venv\Scripts\python -m scripts.test_whatsapp`

Let op: een vrij tekstbericht komt alleen aan binnen 24 uur nadat de ontvanger zelf iets naar
het testnummer stuurde. Daarbuiten is een goedgekeurd sjabloon nodig.

## ngrok

1. Gratis account op ngrok.com, ngrok installeren.
2. Onder *Domains* het gratis vaste domein claimen.
3. `ngrok config add-authtoken <token>` en daarna `ngrok http 8000 --url=<domein>`.
4. `PUBLIEK_ADRES=https://<domein>` in `.env`.

## Twilio

1. Proefaccount op twilio.com.
2. Nummer met Voice (en SMS) kopen. Een Nederlands nummer vraagt om een regulatory bundle
   (adres, soms KvK) en kan dagen duren; een buitenlands nummer werkt direct.
3. Nummer van de eigenaar toevoegen als *Verified Caller ID* (proefaccount belt/sms't alleen daarheen).
4. Account SID, Auth Token en het nummer in `.env`.

## Google Agenda

1. Apart Gmail-account voor OMNIA, agenda *OMNIA demo* aanmaken.
2. console.cloud.google.com → project → *Google Calendar API* aanzetten.
3. Service Account aanmaken → JSON-sleutel downloaden als `google-service-account.json` in `omnia/`.
4. Agenda delen met het e-mailadres van het service account (*Wijzigingen aanbrengen in afspraken*).
5. Agenda-ID uit de agenda-instellingen in `.env`.
