# Order Service


## Odpowiedzialność

Zarządzanie zamówieniami. Przechowuje lokalny read model produktów (ProductSnapshot) zasilany eventami, żeby uniknąć synchronicznych wywołań do product-service przy każdym zamówieniu.

---

## Endpointy REST

Wszystkie endpointy wymagają nagłówka `Authorization: Bearer <token>`.

### `POST /orders/create` 🔒 user

Utworzenie nowego zamówienia z pierwszym produktem.

**Request body:**
```json
{
  "product_id": "uuid",
  "quantity": 2,
  "currency": "USD"
}
```

> Dostępne waluty: `USD`, `PLN`, `EUR`

**Logika:**
1. Sprawdź czy produkt istnieje w `product_snapshots`
2. Sprawdź czy `snapshot.stock >= quantity` — jeśli nie, zwróć `409 Conflict`
3. Utwórz `Order` z `owner_id` z JWT
4. Utwórz `OrderItem` z ceną z snapshotu
5. Opublikuj event `order.created`

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "currency": "USD",
  "order_items": [
    {
      "product_id": "uuid",
      "quantity": 2,
      "order_id": "uuid",
      "price": "25.00"
    }
  ]
}
```

---

### `POST /orders/add-item/{order_id}` 🔒 user

Dodanie produktu do istniejącego zamówienia. Jeśli produkt już jest w zamówieniu, ilość zostaje zsumowana.

**Request body:**
```json
{
  "product_id": "uuid",
  "quantity": 1
}
```

**Logika:**
1. Sprawdź czy zamówienie należy do zalogowanego usera — jeśli nie, zwróć `403 Forbidden`
2. Jeśli produkt już jest w zamówieniu — zaktualizuj ilość, sprawdzając stock
3. Jeśli produkt nowy — utwórz `OrderItem`

**Response `200 OK`:** — pełny obiekt zamówienia jak w `POST /orders/create`

---

### `DELETE /orders/remove-item/{order_id}/{product_id}` 🔒 user

Usunięcie produktu z zamówienia.

**Logika:**
1. Sprawdź czy zamówienie należy do zalogowanego usera — jeśli nie, zwróć `403 Forbidden`
2. Usuń `OrderItem` pasujący do `order_id` + `product_id`

**Response `200 OK`:** — pełny obiekt zamówienia jak w `POST /orders/create`

---

### `POST /orders/pay/{order_id}` 🔒 user

Inicjuje płatność za zamówienie.

**Logika:**
1. Sprawdź czy zamówienie należy do zalogowanego usera — jeśli nie, zwróć `403 Forbidden`
2. Opublikuj event `order.paid`

**Response `200 OK`:** — pełny obiekt zamówienia jak w `POST /orders/create`

---

### `GET /orders/details/{order_id}` 🔒 user

Szczegóły zamówienia.

**Logika:**
1. Sprawdź czy zamówienie należy do zalogowanego usera — jeśli nie, zwróć `403 Forbidden`

**Response `200 OK`:** — pełny obiekt zamówienia jak w `POST /orders/create`

---

## Modele bazy danych

### Tabela: `orders`

| Kolumna | Typ | Ograniczenia |
|--------|-----|-------------|
| `id` | `UUID` | PK |
| `owner_id` | `UUID` | NOT NULL (z JWT, brak FK — inny serwis) |
| `currency` | `ENUM(USD, PLN, EUR)` | NOT NULL |
| `created_at` | `TIMESTAMP` | NOT NULL |
| `updated_at` | `TIMESTAMP` | NOT NULL |

### Tabela: `order_items`

| Kolumna | Typ | Ograniczenia |
|--------|-----|-------------|
| `id` | `UUID` | PK |
| `order_id` | `UUID` | FK → `orders.id` |
| `product_id` | `UUID` | NOT NULL |
| `quantity` | `INTEGER` | NOT NULL |
| `price` | `DECIMAL` | NOT NULL — cena z momentu zamówienia |
| `created_at` | `TIMESTAMP` | NOT NULL |
| `updated_at` | `TIMESTAMP` | NOT NULL |

> Unikalny constraint: `(order_id, product_id)`

### Tabela: `product_snapshots`

Read model zasilany eventami z product-service.

| Kolumna | Typ | Ograniczenia |
|--------|-----|-------------|
| `id` | `UUID` | PK |
| `product_id` | `UUID` | UNIQUE, NOT NULL |
| `stock` | `INTEGER` | NOT NULL |
| `price` | `DECIMAL` | NOT NULL |
| `created_at` | `TIMESTAMP` | NOT NULL |
| `updated_at` | `TIMESTAMP` | NOT NULL |

### Tabela: `outbox`

Transakcyjna skrzynka nadawcza do publikacji eventów.

| Kolumna | Typ | Opis |
|--------|-----|------|
| `id` | `UUID` | PK |
| `event_topic` | `VARCHAR` | Temat eventu |
| `payload` | `JSON` | Dane eventu |
| `status` | `ENUM` | Status przetworzenia (`UNPROCESSED`, ...) |
| `created_at` | `TIMESTAMP` | NOT NULL |
| `updated_at` | `TIMESTAMP` | NOT NULL |

---

## Eventy

### Publikowane

| Event | Wyzwalacz | Payload |
|-------|-----------|---------|
| `order.created` | `POST /orders/create` | `id`, `created_at` |
| `order.paid` | `POST /orders/pay/{order_id}` | `id`, `amount`, `currency`, `paid_at` |

### Konsumowane

| Event | Źródło | Akcja |
|-------|--------|-------|
| `product.created` | product-service | Insert do `product_snapshots` |
| `product.updated` | product-service | Upsert w `product_snapshots` |

---

## Zależności

| Zależność | Cel |
|-----------|-----|
| PostgreSQL | persystencja zamówień i snapshots |
| Broker (Kafka / RabbitMQ) | publikacja eventów przez outbox |
| `shared-lib` | klient brokera, middleware JWT, bazowe modele |
