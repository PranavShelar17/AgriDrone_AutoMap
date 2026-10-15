# Protected API Inventory & Security Policy Matrix

**Document:** API Security Inventory — Phase 9  
**Status:** Implemented & Verified  
**Date:** October 2026  

---

## 1. Overview

This document provides a comprehensive inventory of all REST endpoints exposed by the AgriDrone AutoMap backend (`/api/v1`), specifying authentication requirements, role restrictions, ownership dependency guards, and error responses.

---

## 2. API Endpoints Inventory

### Authentication & User Management (`/auth`)

| Method | Endpoint | Auth Required | Role | Dependency Guard | Failure Response |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `POST` | `/auth/login` | No (Public) | Any | In-memory Rate Limiter | `401 Unauthorized` / `429 Rate Limit` |
| `POST` | `/auth/logout` | Optional | Any | Clears session cookie | `200 OK` |
| `GET` | `/auth/me` | **Yes** | Any | `get_current_user` | `401 Unauthorized` |
| `POST` | `/auth/register-farmer` | **Yes** | Admin Only | `get_current_active_admin` | `401 / 403 Forbidden` |
| `POST` | `/auth/assign-farm` | **Yes** | Admin Only | `get_current_active_admin` | `401 / 403 Forbidden` |
| `POST` | `/auth/status` | **Yes** | Admin Only | `get_current_active_admin` | `401 / 403 Forbidden` |

### Farm Management (`/farms`)

| Method | Endpoint | Auth Required | Role | Dependency Guard | Failure Response |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `GET` | `/farms` | **Yes** | Any | Filtered by `owner_id` for Farmer | `401 Unauthorized` |
| `POST` | `/farms` | **Yes** | Admin / Agronomist | `get_current_active_admin` | `401 / 403 Forbidden` |
| `GET` | `/farms/{id}` | **Yes** | Any | `verify_farm_access` | `401 / 404 Not Found` |
| `PUT` | `/farms/{id}` | **Yes** | Admin Only | `verify_farm_access` + Admin check | `401 / 403 / 404` |
| `DELETE`| `/farms/{id}` | **Yes** | Admin Only | `verify_farm_access` + Admin check | `401 / 403 / 404` |

### Field Management (`/fields`)

| Method | Endpoint | Auth Required | Role | Dependency Guard | Failure Response |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `POST` | `/fields` | **Yes** | Admin / Agronomist | `verify_farm_access` | `401 / 403 / 404` |
| `GET` | `/fields/{id}` | **Yes** | Any | `verify_field_access` | `401 / 404 Not Found` |
| `GET` | `/fields/{id}/boundary` | **Yes** | Any | `verify_field_access` | `401 / 404 Not Found` |

### Survey Flight & Image Ingestion (`/surveys` & `/ingestion`)

| Method | Endpoint | Auth Required | Role | Dependency Guard | Failure Response |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `GET` | `/surveys` | **Yes** | Any | Filtered by owner for Farmer | `401 Unauthorized` |
| `POST` | `/surveys` | **Yes** | Admin / Agronomist | `verify_field_access` | `401 / 403 / 404` |
| `GET` | `/surveys/{id}` | **Yes** | Any | `verify_survey_access` | `401 / 404 Not Found` |
| `POST` | `/ingestion/surveys/{id}/files` | **Yes** | Admin / Agronomist | `verify_survey_access` + Admin check | `401 / 403 Forbidden` |
| `GET` | `/ingestion/surveys/{id}/files` | **Yes** | Any | `verify_survey_access` | `401 / 404 Not Found` |
| `DELETE`| `/ingestion/files/{id}` | **Yes** | Admin / Agronomist | `get_current_active_admin` | `401 / 403 Forbidden` |
| `GET` | `/ingestion/files/{id}/download`| **Yes** | Any | `verify_survey_access` | `401 / 404 Not Found` |

### Photogrammetry Reconstruction (`/photogrammetry`)

| Method | Endpoint | Auth Required | Role | Dependency Guard | Failure Response |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `POST` | `/photogrammetry/tasks` | **Yes** | Admin / Agronomist | `verify_survey_access` + Admin check | `401 / 403 Forbidden` |
| `GET` | `/photogrammetry/tasks` | **Yes** | Any | Filtered by owner for Farmer | `401 Unauthorized` |
| `GET` | `/photogrammetry/tasks/{id}` | **Yes** | Any | `verify_task_access` | `401 / 404 Not Found` |
| `GET` | `/photogrammetry/eligible-surveys` | **Yes** | Any | Filtered by owner for Farmer | `401 Unauthorized` |

### GIS Algorithms & Vegetation Indices (`/algorithms`)

| Method | Endpoint | Auth Required | Role | Dependency Guard | Failure Response |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `GET` | `/algorithms/eligible-products` | **Yes** | Any | Filtered by owner for Farmer | `401 Unauthorized` |
| `POST` | `/algorithms/batch` | **Yes** | Admin / Agronomist | `verify_survey_access` + Admin check | `401 / 403 Forbidden` |
| `GET` | `/algorithms/jobs` | **Yes** | Any | Filtered by owner for Farmer | `401 Unauthorized` |
| `GET` | `/algorithms/jobs/{id}` | **Yes** | Any | `verify_algorithm_job_access` | `401 / 404 Not Found` |
| `GET` | `/algorithms/batches/{id}/status`| **Yes** | Any | `verify_survey_access` | `401 / 404 Not Found` |
| `GET` | `/algorithms/products/{id}` | **Yes** | Any | `verify_map_product_access` | `401 / 404 Not Found` |

### Interactive Maps & Diagnostics (`/maps`)

| Method | Endpoint | Auth Required | Role | Dependency Guard | Failure Response |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `GET` | `/maps/fields/{id}/boundary` | **Yes** | Any | `verify_field_access` | `401 / 404 Not Found` |
| `GET` | `/maps/surveys/{id}/coverage` | **Yes** | Any | `verify_survey_access` | `401 / 404 Not Found` |
| `GET` | `/maps/surveys/{id}/products` | **Yes** | Any | `verify_survey_access` | `401 / 404 Not Found` |
| `GET` | `/maps/products/{id}/visualization`| **Yes** | Any | `verify_map_product_access` | `401 / 404 Not Found` |
| `GET` | `/maps/tiles/{id}/{z}/{x}/{y}.png`| **Yes** | Any | `get_current_user_with_query_fallback` + `verify_map_product_access` | `401 / 404 Not Found` |
| `GET` | `/maps/products/{id}/probe` | **Yes** | Any | `verify_map_product_access` | `401 / 404 Not Found` |
| `GET` | `/maps/products/{id}/diagnostics` | **Yes** | Any | `verify_map_product_access` | `401 / 404 Not Found` |
| `GET` | `/maps/compare-compatibility` | **Yes** | Any | `verify_map_product_access` (both A & B) | `401 / 404 Not Found` |

### Reports & Deliverables (`/reports`)

| Method | Endpoint | Auth Required | Role | Dependency Guard | Failure Response |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `GET` | `/reports` | **Yes** | Any | Filtered by owner for Farmer | `401 Unauthorized` |
| `GET` | `/reports/{id}` | **Yes** | Any | `verify_report_access` | `401 / 404 Not Found` |
| `GET` | `/reports/{id}/download` | **Yes** | Any | `verify_report_access` | `401 / 404 Not Found` |
