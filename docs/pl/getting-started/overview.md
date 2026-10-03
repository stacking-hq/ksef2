---
title: Wprowadzenie
description: Punkt startowy dokumentacji ksef2 — typowanego SDK Pythona do integracji z KSeF 2.0.
---

![ksef2](../../../sdk/assets/logo-dark.png)

**ksef2** to w pełni typowane SDK dla języka Python do integracji z API systemu KSeF 2.0.

> **Nieoficjalne SDK.** ksef2 jest projektem open-source utrzymywanym przez społeczność. \
> Nie jest publikowany, zatwierdzany ani wspierany przez Ministerstwo Finansów. \
> Oficjalna dokumentacja KSeF pozostaje źródłem informacji o działaniu systemu oraz zasadach pracy z nim.

[Oficjalna dokumentacja API KSeF v2](https://api-test.ksef.mf.gov.pl/docs/v2/) — Tutaj znajdziesz oficjalną dokumentację API KSeF 2.0, na której opiera się biblioteka ksef2.

Projekt powstał z myślą o osobach, które budują własne integracje,
automatyzacje i narzędzia back-office wokół KSeF, ale nie chcą ręcznie
odtwarzać logiki HTTP, pętli odpytywania ani obsługi szyfrowania.

Głównym założeniem SDK jest umożliwienie pracy z systemem KSeF przez wygodny
interfejs, który podąża za praktykami i wzorcami typowymi dla języka Python.

Pozwala to skupić się na logice biznesowej zamiast na szczegółach API KSeF.
Biblioteka ukrywa wiele szczegółów komunikacji z systemem, ale nie zamyka drogi
do niższego poziomu. Jeśli potrzebujesz większej kontroli nad żądaniami i
odpowiedziami, możesz użyć niskopoziomowego dostępu do endpointów.

## Następne kroki

- [Szybki start](../getting-started/quickstart.md): Zacznij od działającego przykładu uwierzytelniania, wysyłania, wyszukiwania i pobierania faktur.
- [Jak działa SDK](../concepts/overview.md): Poznaj model klientów, uwierzytelnianie i przepływy faktur w bibliotece.
- [Wysyłanie, wyszukiwanie i pobieranie faktur](../how-to-guides/overview.md): Zobacz, jak wysyłać faktury online albo w trybie batch, wyszukiwać je z filtrami i paginacją oraz pobierać bezpośrednio albo jako pakiety eksportu.
- [API niskopoziomowe](../reference/low-level/overview.md): Użyj wrapperów endpointów zgodnych ze schematem, kiedy potrzebujesz bezpośredniej kontroli.
