# Specyfikacja Techniczna Projektu: Automatyczny pomiar funkcji HRTF

## 1. Model UML projektowanego rozwiązania
*(W tym miejscu diagram komponentów oraz diagram klas)*

Architektura systemu opiera się na rozdziale warstwy sterującej (komputer PC) oraz wykonawczej (Arduino). Zgodnie z opracowanym diagramem klas, kluczowe elementy systemu to:
* Modelowanie sprzętu: Klasa `ArduinoConnection` odpowiadająca za protokół UART oraz klasy obsługujące interfejs audio.
* Logika pomiarowa: `HRIRMeasurement` obsługująca akwizycję i dekonwolucję sygnału, a także algorytmy generowania siatki sferycznej.
Rozwiązanie zapewnia modułowość – logika sterowania silnikami jest odseparowana od toru przetwarzania sygnałów audio.

## 2. Analiza bibliotek i narzędzi
Projekt wykorzystuje następujący stos technologiczny:

**Narzędzia i biblioteki bazowe (już zaimplementowane):**
* Języki programowania: **Python** (aplikacja PC), **C++** (mikrokontroler Arduino).
* **Numpy:** Wykorzystywana do zaawansowanych obliczeń matematycznych (np. generowanie punktów na sferze metodą Deserno).
* **Scipy:** Niezbędna do cyfrowego przetwarzania sygnałów (operacje splotu/dekonwolucji oraz aplikacja okien wygładzających Tukeya).
* **Sounddevice & Soundfile:** Używane do jednoczesnego odtwarzania sygnału typu sweep-sine i rejestracji odpowiedzi z mikrofonów.
* **Pyserial:** Umożliwia asynchroniczną komunikację szeregową PC <-> Arduino.
* **Matplotlib:** Służy do wizualizacji siatki wygenerowanych punktów pomiarowych.

**Dodatkowe narzędzia do realizacji założeń POS:**
* **pdoc / Sphinx:** Biblioteki posłużą do automatycznego generowania dokumentacji HTML wprost z komentarzy (docstringów) dodanych do klas i metod.
* **pytest:** Framework wybrany do realizacji i automatyzacji testów jednostkowych (np. walidacji funkcji wyliczających liczbę kroków silnika).
* **cProfile:** Wbudowany w Pythona profiler posłuży do poszukiwania "hot spotów" wydajnościowych (m.in. w algorytmach splotu sygnałów audio).

## 3. Harmonogram i podział pracy w zespole
Prace nad dostosowaniem oprogramowania do wymogów przedmiotu POS zostały podzielone w następujący sposób:

**Piotr (Maintainer):**
1. Zarządzanie repozytorium GitHub, utrzymanie czystości gałęzi głównej oraz ewidencja zadań w systemie Issues.
2. Zaimplementowanie testów jednostkowych (`pytest`) dla krytycznych operacji logicznych i matematycznych.
3. Analiza wydajności za pomocą profilera (`cProfile`) oraz ewentualna optymalizacja zidentyfikowanych wąskich gardeł w kodzie.

**Hubert:**
1. Refaktoryzacja obecnego skryptu liniowego na pełnoprawną architekturę zorientowaną obiektowo (OOP), zgodnie ze stworzonym diagramem klas.
2. Opracowanie szczegółowej dokumentacji API (docstringi) i wygenerowanie ostatecznej dokumentacji w formacie HTML.
3. Utrzymanie poprawnej komunikacji z warstwą sprzętową (Arduino i mikser audio) po zmianie struktury kodu.