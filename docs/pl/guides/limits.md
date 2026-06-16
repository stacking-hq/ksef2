---
title: Limity
description: Odczyt i modyfikacja limitów w środowisku TEST.
---

Limity są dostępne przez `auth.limits`. Operacje modyfikujące są przeznaczone
dla środowiska TEST.

```python
context_limits = auth.limits.get_context_limits()
subject_limits = auth.limits.get_subject_limits()
api_limits = auth.limits.get_api_rate_limits()
```

## Zmiana limitów

```python
auth.limits.set_session_limits(limits=context_limits)
auth.limits.reset_session_limits()
```

## Limity produkcyjne w TEST

```python
auth.limits.set_production_rate_limits()
```

Używaj tego, gdy chcesz sprawdzić zachowanie aplikacji pod limitami zbliżonymi
do produkcyjnych.
