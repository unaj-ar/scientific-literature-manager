# 📋 Project Assessment: Scientific Literature Manager

## 1. Executive Summary
The **Scientific Literature Manager** is a lightweight, relational database-backed CLI application designed to streamline the academic research lifecycle. It systematically covers the core stages of literature management: **Discovery**, **Organization**, **Prioritization**, and **Retrieval**.

---

## 2. Problem Statement & Solution

### ⚠️ Problem
Academic researchers face information overload when collecting scientific papers. Key friction points include:
* Disorganized reference storage across local file systems.
* Difficulty prioritizing reading lists.
* Lack of normalized author metadata, leading to duplicate entries and complex retrieval.
* Inability to quickly query articles written by a specific author.

### 💡 Solution
A Python CLI application integrated with PostgreSQL that:
1. Normalizes author records into a dedicated table using a **Many-to-Many (`N:M`)** entity relationship.
2. Implements domain-level input validation to guarantee database integrity (e.g., restricted statuses and priorities via `CHECK` constraints).
3. Provides flexible, case-insensitive keyword searches (`ILIKE`) for efficient literature retrieval.

---

## 3. Technical Architecture & Stack

* **Language:** Python 3.10+
* **Database Engine:** PostgreSQL 14+
* **Database Driver:** `psycopg2-binary` (using `RealDictCursor` for dictionary mapping)
* **Architecture Pattern:** CLI Interface with Data Access Objects (DAO-style functions)

---

## 4. Entity-Relationship Model (ERD)

The database structure relies on three core tables to maintain 3rd Normal Form (3NF):