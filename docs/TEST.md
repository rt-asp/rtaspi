
# Wytyczne do pisania testów jednostkowych dla projektu RTASPI

## Ogólne zasady struktury testów

1. Testy powinny być zorganizowane w sposób modułowy, wykorzystując parametryzację i fixtury pytest.
2. Każdy plik testowy powinien koncentrować się na testowaniu jednego modułu lub komponentu.
3. Stosuj standardowy prefiks `test_` dla funkcji testowych.

## Formatowanie i organizacja plików testowych

```python
import pytest
from unittest.mock import MagicMock, patch
# Importuj inne potrzebne moduły

# Stałe testowe - zdefiniowane na początku pliku
TEST_DATA = {...}
PARAM_VALUES = [...]

# Parametryzowane fixtury
@pytest.fixture(params=PARAM_VALUES)
def parametrized_fixture(request):
    # Zwróć wartość na podstawie parametru
    return request.param

# Ogólne fixtury
@pytest.fixture
def common_fixture():
    # Konfiguruj i zwróć mockowany obiekt lub dane testowe
    return ...

# Testy jednostkowe z odpowiednimi markerami
@pytest.mark.unit
@pytest.mark.module_name  # np. discovery, streaming, device
def test_specific_functionality(fixture):
    # Test dla konkretnej funkcjonalności
    ...

# Parametryzowane testy
@pytest.mark.unit
@pytest.mark.parametrize("input_value,expected_output", [
    (value1, expected1),
    (value2, expected2),
])
def test_parametrized(input_value, expected_output):
    # Test z różnymi wartościami wejściowymi
    ...

# Testy asynchroniczne
@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_function():
    # Test dla funkcji asynchronicznej
    ...
```

## Wymagane markery testów

Każdy test powinien mieć co najmniej dwa markery:
1. Marker poziomu (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.system`)
2. Marker modułu (`@pytest.mark.discovery`, `@pytest.mark.streaming`, `@pytest.mark.device_manager` itp.)

Dodatkowe markery dla testów specjalistycznych:
- `@pytest.mark.asyncio` - dla testów funkcji asynchronicznych
- `@pytest.mark.slow` - dla testów wymagających więcej czasu
- `@pytest.mark.requires_network` - dla testów wymagających połączenia sieciowego

## Wykorzystanie parametryzacji i redukcja duplikacji

Preferuj parametryzację zamiast powielania podobnych testów. Przykład:

```python
# Dane parametryzujące na początku pliku
MODULE_TYPES = [
    (Module1, "type1", param1),
    (Module2, "type2", param2),
]

@pytest.mark.unit
@pytest.mark.parametrize("module_class,module_type,param", MODULE_TYPES)
def test_module_functionality(module_class, module_type, param):
    module = module_class()
    # Test wspólnej funkcjonalności
```

## Mockowanie zależności

Zawsze używaj mocków dla zewnętrznych zależności:

```python
@pytest.mark.unit
def test_with_dependency():
    with patch("module.external_dependency") as mock_dep:
        mock_dep.return_value = expected_value
        # Test z zależnością
```

## Testowanie przypadków brzegowych

Zawsze uwzględniaj różne przypadki brzegowe, najlepiej z wykorzystaniem parametryzacji:

```python
@pytest.mark.unit
@pytest.mark.parametrize("test_case", [
    {"input": valid_input, "expected": valid_output, "desc": "Valid case"},
    {"input": empty_input, "expected": default_output, "desc": "Empty input"},
    {"input": invalid_input, "raises": ValueError, "desc": "Invalid input"},
])
def test_edge_cases(test_case):
    if "raises" in test_case:
        with pytest.raises(test_case["raises"]):
            function(test_case["input"])
    else:
        result = function(test_case["input"])
        assert result == test_case["expected"]
```

## Testowanie asynchroniczne

Dla testów asynchronicznych używaj dedykowanego markera i odpowiednich wzorców:

```python
@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_function():
    # Bezpośrednie testowanie funkcji async
    result = await async_function()
    assert result == expected

    # Lub z wykorzystaniem asyncio.gather dla równoległych operacji
    results = await asyncio.gather(
        async_function1(),
        async_function2()
    )
    assert results[0] == expected1
    assert results[1] == expected2
```

## Obsługa błędów i wyjątków

Testy powinny zawsze weryfikować, czy funkcje odpowiednio obsługują błędy:

```python
@pytest.mark.unit
def test_error_handling():
    with pytest.raises(ExpectedException) as exc_info:
        function_that_raises()
    assert "expected error message" in str(exc_info.value)
```

## Nazewnictwo testów

Używaj opisowych nazw funkcji testowych, które jasno wskazują co jest testowane:
- `test_module_initialization`
- `test_function_with_valid_input`
- `test_function_error_handling`
- `test_specific_edge_case`

Przestrzeganie tych wytycznych zapewni spójność, utrzymywalność i czytelność testów w całym projekcie RTASPI.