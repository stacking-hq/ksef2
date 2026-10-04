---
title: Sesje
description: Zrozum stan sesji online, batch, uwierzytelniania i historii sesji w ksef2.
---

Sesja KSeF jest zdalnym kontenerem przepływu. Grupuje kilka wywołań API pod
jednym numerem referencyjnym, aby KSeF mógł przetworzyć zaszyfrowane faktury,
udostępnić status i wystawić dokumenty UPO po zakończeniu pracy.

W SDK obiekt sesji jest uchwytem do tego zdalnego przepływu. Nie jest źródłem
prawdy. Źródłem prawdy jest numer referencyjny sesji i status zwracany przez
KSeF dla tej referencji.

```text
klient uwierzytelniony
  -> otwarcie sesji online albo batch
    -> numer referencyjny sesji
      -> wysyłka/upload zaszyfrowanych danych faktury
        -> status, wyniki faktur, UPO
```

## Rodziny sesji

KSeF ma kilka powierzchni przypominających sesje. Odpowiadają na różne pytania
i są dostępne przez różne gałęzie SDK.

| Rodzina sesji | Gałąź SDK | Co reprezentuje |
| --- | --- | --- |
| Sesja faktur online | `auth.online_session()` | Krótki interaktywny przepływ dla wysyłki jednej albo kilku faktur. |
| Sesja faktur batch | `auth.batch_session()` albo `auth.batch` | Przepływ uploadu zaszyfrowanej paczki ZIP podzielonej na części. |
| Sesja uwierzytelniania | `auth.sessions` | Aktywne sesje bearer-token utworzone przez uwierzytelnianie. |
| Historia sesji faktur | `auth.invoice_sessions` | Historyczne sesje faktur online i batch, które można odpytać po zakończeniu pierwotnego procesu. |

Pierwsze dwie rodziny są przepływami wysyłki faktur. Sesje uwierzytelniania i
historia sesji faktur służą do inspekcji albo administracji.

## Sesje online

Sesja online jest interaktywną ścieżką wysyłki. Otwiera się ją dla schematu
formularza, na przykład `FormSchema.FA3`, a potem wysyła faktury pojedynczo do
tej sesji.

Otwarcie sesji jest lekką operacją. SDK ładuje publiczny certyfikat szyfrowania
KSeF, tworzy materiał szyfrowania sesji, otwiera zdalną sesję i zwraca
`OnlineSessionClient` przypisany do zwróconego `reference_number`.

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    state = session.resume_state()
    print(state.reference_number, state.valid_until)
```

Klienta sesji online używaj do wywołań powiązanych z fakturami wysłanymi w tej
sesji: wysyłki, listy faktur sesji, sprawdzenia jednej faktury i pobrania UPO po
referencji faktury albo numerze KSeF.

Context manager wywołuje `close()` przy wyjściu z bloku. Zamknięcie sesji online
informuje KSeF, że nie będzie już kolejnych faktur, i pozwala wygenerować
zbiorcze UPO dla sesji.

:::tip[Zapisuj przed granicą procesu]
Zapisz referencję sesji i referencje faktur przed długim pollingiem,
przekazaniem pracy do kolejki albo zakończeniem procesu. Obiekt Pythona można
odtworzyć; referencje KSeF są tym, co pozwala innemu workerowi wznowić
inspekcję.
:::

## Wznawianie sesji

`online_session()` i `batch_session()` otwierają sesję albo ją wznawiają, tą samą
metodą. Podaj dokładnie jedną formę: `form_code=` (albo `prepared_batch=` /
`batch_file=`), by otworzyć, lub `state=`, by wznowić. `state=` przyjmuje obiekt
stanu albo jego JSON, a wszystko (kod formularza, klucze, ważność, żądania
uploadu) pochodzi ze stanu.

```python
with auth.online_session(form_code=FormSchema.FA3) as session:
    saved = session.resume_state().to_json()      # przechowuj jak poświadczenie
    reference = session.send_invoice(xml).reference_number

# później, możliwe że w innym procesie
with auth.online_session(state=saved) as session:
    status = session.submission(reference).wait()  # uchwyt wcześniej wysłanej faktury
```

Wyjście z bloku `with` zamyka sesję w obu przypadkach. Zamknięcie już zamkniętej
sesji nic nie robi: wznowiony klient najpierw pyta KSeF, więc nie wysyła drugiego
żądania zamknięcia. Sesje batch działają tak samo z `auth.batch_session(state=saved)`,
a potem `session.wait()` i `session.download_upo()`. `resume_online_session()` i
`resume_batch_session()` są wycofanymi aliasami. Stan sesji zawiera klucze
szyfrowania: nigdy go nie loguj.

Wznowione uchwyty sesji, joby `invoices.export(state=...)` i reszta klienta
uwierzytelnionego współdzielą jeden transport, więc wszystkie używają bieżącego
access tokenu klienta i odświeżają go w razie potrzeby (zobacz
[Access tokeny odświeżają się same](authentication-methods.md#access-tokeny-odświeżają-się-same)).
Wznowiony klient z wygasłym access tokenem działa, dopóki jego refresh token jest
ważny. Jeśli wygasł także refresh token, wywołanie rzuca
`KSeFAuthenticationExpiredError`: uwierzytelnij się ponownie, a potem wznów sesję
z zapisanego stanu.

## Sesje batch

Sesja batch jest ścieżką wysyłki masowej. Jednostką wysyłaną do KSeF nie jest
pojedynczy plik XML. Jest nią przygotowana paczka ZIP zawierająca pliki XML
faktur, podzielona na części i zaszyfrowana przed uploadem.

Normalny przepływ obsługuje wysokopoziomowy serwis `auth.batch`:

1. Zbuduj paczkę ZIP z plików XML faktur albo z bajtów faktur w pamięci.

2. Podziel paczkę na części przed szyfrowaniem.

3. Zaszyfruj każdą część i policz metadane paczki oraz części.

4. Otwórz sesję batch i odbierz instrukcje uploadu.

5. Wgraj wszystkie części, zamknij sesję i polluj status.

```python
prepared = auth.batch.prepare([Path("invoice-1.xml"), Path("invoice-2.xml")])

session = auth.batch.submit(prepared)
print(session.reference_number)
```

Dla przepływów batch zachowaj mapowanie między lokalnymi plikami źródłowymi a
metadanymi przygotowanych faktur. KSeF raportuje wyniki poszczególnych faktur
przez pola statusu faktury w sesji, takie jak `invoice_hash`,
`invoice_file_name`, `reference_number` i późniejszy `ksef_number`.

## Stan, status i historia

Te trzy pojęcia łatwo pomylić:

| Pojęcie | Znaczenie | Kształt SDK |
| --- | --- | --- |
| Stan | Lokalne dane potrzebne do odtworzenia uchwytu sesji. Zawiera wrażliwy materiał szyfrowania sesji i, dla batcha, URL-e uploadu. | `OnlineSessionResumeState`, `BatchSessionResumeState` |
| Status | Aktualny obraz zdalnego przepływu po stronie KSeF. To on mówi, czy przetwarzanie się udało, nie udało albo nadal trwa. | `SessionStatusResponse`, `SessionInvoiceStatusResponse` |
| Historia | Lista poprzednich sesji online albo batch. Użyj jej, gdy nie masz już pierwotnego lokalnego obiektu. | `auth.invoice_sessions` |

Stan sesji przydaje się do wznawiania operacji SDK, ale jest wrażliwy. Nie
wypisuj go i nie zapisuj w logach. Do audytu i wsparcia zapisuj odpowiedzi
statusowe oraz historię sesji.

```python
status = session.get_status()
print(
    status.status.code,
    status.invoice_count,
    status.successful_invoice_count,
    status.failed_invoice_count,
)
```

## Co zapisywać

Zapisz co najmniej:

- numer referencyjny sesji;
- numer referencyjny faktury zwrócony po wysyłce;
- numer KSeF po akceptacji;
- hash faktury albo nazwę pliku do korelacji batch;
- referencję UPO albo pobrane bajty UPO, gdy są dostępne;
- lokalny correlation id z własnego systemu.

Sesja KSeF może żyć dłużej niż proces Pythona, który ją otworzył. Trwały zapis
tych identyfikatorów umożliwia ponowienia, późniejsze pobranie UPO i analizę
zgłoszeń.

## Powiązane strony

- [Wyślij faktury](../how-to-guides/send-invoices.md): Otwórz sesję online albo batch i wyślij XML faktury.
- [Sprawdź status i UPO](../how-to-guides/get-status-and-upo.md): Polluj status sesji i faktury, a potem pobierz dokument UPO.
- [Cykl życia faktury](invoice-lifecycle.md): Prześledź fakturę od wysyłki XML do numeru KSeF, metadanych, pobrania i UPO.
- [Low-level sesje i faktury](../reference/low-level/sessions-invoices.md): Zobacz bazowe endpointy sesji i faktur.
