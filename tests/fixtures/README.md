# Parsing fixtures

Public bookstore responses captured on 2026-10-03 (Asia/Seoul):

- YES24 Goods `125557465`, ISBN `9791171711673` and ISBN search.
- Kyobo Product `S000000610625`, ISBN `9788936434267`, ISBN search and product middle API.

Fixtures preserve bibliographic fields and response structures. Long introductions and reviews were shortened. Kyobo uses Next.js Flight JSON string chunks; the adapter selects only the requested product ID.
