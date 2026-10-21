---
title: "Jak połączyć testy umiejętności z ATS"
seoTitle: "Jak połączyć testy umiejętności z ATS: praktyczny poradnik"
description: "Wysyłaj testy umiejętności i odbieraj wyniki automatycznie przez ATS, zostaw decyzje rekrutacyjne ludziom i sprawdź, na co zwrócić uwagę najpierw."
updated: "2026-10-21"
---

# Jak połączyć testy umiejętności z ATS

Większość zespołów rekrutacyjnych prowadzi kandydatów w systemie ATS (applicant tracking system), a testy umiejętności przeprowadza w innym narzędziu. Bez połączenia między nimi ktoś kopiuje adresy e-mail z ATS, ręcznie wysyła zaproszenia, czeka, a potem przenosi wyniki z powrotem. Przy pięciu kandydatach to działa. Przy pięćdziesięciu zaproszenia wychodzą z opóźnieniem, wyniki leżą w drugiej karcie, której nikt nie otwiera, a dobrzy kandydaci w czasie oczekiwania przyjmują inne oferty.

Ten poradnik wyjaśnia, co robi dobre połączenie ATS z narzędziem do testów, co sprawdzić, zanim zaczniesz na nim polegać, i jak je skonfigurować, żeby automatyzacja przejęła żmudną pracę, a każdą decyzję rekrutacyjną nadal podejmowali ludzie.

## Po co je w ogóle łączyć

| Bez integracji | Z integracją |
| --- | --- |
| Ktoś eksportuje lub kopiuje adresy e-mail kandydatów | Przeniesienie kandydata na etap wysyła zaproszenie |
| Zaproszenia wychodzą, gdy ktoś ma czas | Zaproszenia wychodzą w ciągu kilku minut od przeniesienia |
| Wyniki są w narzędziu do testów | Wyniki pojawiają się przy kandydacie w ATS |
| Rekrutujący menedżerowie pytają: „Czy ktoś ich już sprawdził?” | ATS pokazuje, kto zrobił test i z jakim wynikiem |
| Literówki w adresach i pominięci kandydaci | ATS to jedna lista wszystkich, którzy aplikowali |

Szybkość ma większe znaczenie, niż się wydaje. Im dłużej kandydat czeka na odpowiedź po aplikacji, tym więcej osób rezygnuje albo przyjmuje inną pracę. Dokładny odsetek rezygnacji mocno zależy od stanowiska i rynku, więc do publikowanych liczb podchodź ostrożnie, ale kierunek jest stały: powolny proces traci ludzi, a najlepsi kandydaci zwykle mają najwięcej możliwości.

## Jak wygląda dobry proces

Dobra integracja podąża za etapami, których już używasz. Nie wymyśla nowego procesu.

1. **Kandydat aplikuje** i jak zwykle trafia do ATS.
2. **Ktoś z zespołu przenosi go na etap testu,** na przykład „Test umiejętności”. To przeniesienie uruchamia proces, więc o tym, kto dostanie test, nadal decyduje człowiek.
3. **Narzędzie do testów wysyła zaproszenie** automatycznie, do testu przypisanego do tej oferty pracy.
4. **Kandydat rozwiązuje test** w dogodnym dla siebie czasie, w wyznaczonym przez Ciebie terminie.
5. **Wyniki trafiają z powrotem do kandydata w ATS:** wynik punktowy, informacja, czy zdał, ewentualne sygnały nieuczciwości i link do pełnych odpowiedzi.
6. **Człowiek przegląda wynik** i przenosi kandydata dalej albo nie.

Dwie rzeczy celowo pozostają ręczne: wybór, kto dostanie test, i decyzja, co dalej. Integracja usuwa tylko kopiowanie pomiędzy nimi.

### Dlaczego nie wysyłać testu przy każdej nowej aplikacji?

Niektóre narzędzia zapraszają każdego, kto aplikuje. To może się sprawdzić przy rekrutacjach masowych, gdzie wszyscy kandydaci robią ten sam test. Ale etap, na który przenosisz kandydatów, łatwiej kontrolować: możesz pominąć osoby, które wyraźnie nie spełniają twardego wymogu (brak pozwolenia na pracę, inna lokalizacja), i nigdy nie testujesz — ani nie płacisz za — kogoś, kogo i tak zamierzałeś odrzucić.

## Co sprawdzić przed wyborem integracji

Nie każde zapewnienie „integruje się z Twoim ATS” oznacza to samo. Zadaj te pytania, zanim cokolwiek połączysz.

| Pytanie | Dlaczego to ważne | Dobra odpowiedź |
| --- | --- | --- |
| Jak odbywa się połączenie? | Wspólne hasła i konta trzymane przez dostawcę trudno kontrolować i odwołać | Klucz API lub token, który tworzy Twoja firma i może w każdej chwili usunąć |
| Co może zrobić klucz? | Klucz z pełnym dostępem jest ryzykiem, jeśli wycieknie | Najwęższe uprawnienia potrzebne integracji, wymienione w dokumentacji |
| Co uruchamia zaproszenie? | Musisz dokładnie wiedzieć, kiedy kandydaci dostają e-maile | Konkretny etap, który wybierasz dla każdej oferty pracy |
| Gdzie trafiają wyniki? | Wyniki, których nikt nie widzi, nic nie dają | Do profilu kandydata, jako notatka lub komentarz, które Twój zespół i tak czyta |
| Co się dzieje, gdy zaproszenie nie wyjdzie? | Brak kredytów, literówka, wstrzymane konto: kandydaci utykają bez słowa | Ktoś dostaje informację, a kandydata można zaprosić ponownie |
| Czy zdarzenie może zostać przetworzone dwa razy? | ATS wysyłają zdarzenia ponownie; kandydat nie powinien dostać dwóch zaproszeń | Każdy kandydat jest zapraszany na test raz, niezależnie od tego, ile razy przyjdzie zdarzenie |
| Jak weryfikowane są przychodzące zdarzenia? | Na niezweryfikowany adres można wysłać fałszywe zdarzenia | Podpisane żądania, które narzędzie sprawdza |
| Jak długo przechowywane są dane kandydatów? | Przepisy o ochronie danych, takie jak RODO, wymagają jasnego okresu przechowywania | Podany okres i usunięcie danych wraz z ofertą pracy, testem lub kontem |
| Ile to kosztuje? | Plany płatne za użytkownika mogą sprawić, że automatyzacja będzie droga | Przewidywalny koszt za każdego przetestowanego kandydata |

Jeśli dostawca nie potrafi jasno odpowiedzieć na pytania o błędy i duplikaty, spodziewaj się, że przekonasz się o tym na własnej skórze.

### Ochrona danych

Połączenie dwóch systemów oznacza, że dane kandydatów, co najmniej imiona i nazwiska oraz adresy e-mail, przepływają między dwiema firmami. Zgodnie z RODO i podobnymi przepisami dostawca testów jest zwykle podmiotem przetwarzającym, więc potrzebujesz umowy powierzenia przetwarzania danych i powinieneś poinformować kandydatów, w klauzuli informacyjnej lub w zaproszeniu, że test umiejętności jest częścią procesu. Przekazuj tylko te dane, których test naprawdę potrzebuje. Więcej o prawnej stronie testów i AI w rekrutacji przeczytasz w artykule [Czy rekrutacja z AI jest legalna w UE?](/guides/is-ai-hiring-legal-in-the-eu)

## Lista kontrolna konfiguracji

Zanim włączysz integrację dla prawdziwej rekrutacji:

1. **Utwórz w ATS osobny etap na test,** na przykład „Test umiejętności”. Nie używaj etapu, który oznacza coś innego, bo kandydaci będą dostawać zaproszenia przez przypadek.
2. **Utwórz klucz z konta administratora,** które widzi wszystkie oferty pracy, które chcesz połączyć, i tylko z uprawnieniami wymienionymi w dokumentacji.
3. **Powiąż każdą ofertę pracy z jej testem** i wybierz etap, który uruchamia zaproszenie.
4. **Skonfiguruj webhook,** jeśli Twój ATS wymaga zrobienia tego ręcznie, i wklej jego sekret tam, gdzie prosi o to narzędzie.
5. **Przetestuj na sobie.** Dodaj kandydata ze swoim adresem e-mail, przenieś go na etap, rozwiąż test i sprawdź, czy notatka pojawiła się w ATS.
6. **Ustal, kto pilnuje błędów:** kto dostaje informację, gdy zaproszenia nie da się wysłać, i kto to naprawia.
7. **Uzgodnijcie, jak czytać wyniki.** Próg zaliczenia to wskazówka, a nie automatyczne odrzucenie. Ustalcie to, zanim przyjdą wyniki, a nie po.

## Częste błędy

- **Automatyzowanie decyzji zamiast papierologii.** Automatyczne odrzucanie wszystkich poniżej progu usuwa ludzką kontrolę, która wyłapuje źle sformułowane pytanie albo kandydata z problemem z połączeniem. Niech wynik sortuje, a decyduje człowiek.
- **Uruchamianie z niewłaściwego etapu.** Etap, którego rekruterzy używają do innych celów, wysyła testy osobom, które nie powinny ich dostać.
- **Jeden test na każde stanowisko.** Integracja ułatwia wysyłanie tego samego testu wszędzie. A test pomaga najbardziej, gdy jest przygotowany pod konkretne stanowisko. Zobacz [Testy umiejętności a selekcja CV](/guides/skills-tests-vs-cv-screening).
- **Nikt nie pilnuje błędów.** Jeśli zaproszenie po cichu nie wyjdzie, kandydat czeka na e-mail, który nigdy nie przyjdzie, a Ty myślisz, że go zignorował.
- **Klucz powiązany z osobą, która odchodzi.** Niektóre klucze ATS działają w imieniu osoby, która je utworzyła. Gdy jej konto zostanie zamknięte, integracja przestaje działać. Używaj konta, które zostanie, i łącz integrację ponownie, gdy ludzie zmieniają role.
- **Zapominanie o kandydatach spoza ATS.** Kandydaci z poleceń i osoby aplikujące bezpośrednio, którzy nigdy nie trafiają do ATS, też potrzebują zaproszenia. Zachowaj również ręczny sposób zapraszania.

## Jak robi to prepza

prepza łączy się z **Workable, Greenhouse, Teamtailor, Recruitee i Breezy HR**. Działa według opisanego wyżej procesu.

- **Twój klucz, Twoja kontrola.** Właściciel lub administrator łączy ATS w zakładce Integracje firmy za pomocą klucza, który Twoja firma tworzy w ATS. prepza sprawdza go przed zapisaniem, przechowuje zaszyfrowany i nigdy więcej go nie pokazuje. Odłączenie od razu usuwa klucz i powiązane oferty pracy.
- **Powiąż ofertę pracy z rozmową.** Wybierz ofertę pracy w ATS i etap, który uruchamia zaproszenie, a następnie powiąż ją z istniejącą rozmową w prepza albo utwórz nową na podstawie treści ogłoszenia z ATS. Sprawdzasz tematy, zanim powstanie jakiekolwiek pytanie.
- **Przenosisz kandydata, zaproszenie wychodzi.** Każdy kandydat jest zapraszany na rozmowę raz, nawet jeśli ATS wyśle to samo zdarzenie dwa razy.
- **Wyniki wracają do ATS.** Gdy kandydat skończy, prepza dodaje przy nim w ATS notatkę lub komentarz z oceną, informacją, czy zdał, ewentualnymi sygnałami nieuczciwości (opuszczenie strony, próby kopiowania, odpowiedzi wybrane zbyt szybko, by zdążyć przeczytać pytanie) i linkiem do jego karty wyników ze wszystkimi odpowiedziami.
- **Błędy nie przechodzą niezauważone.** Jeśli kandydata nie da się zaprosić, na przykład dlatego, że firmie skończyły się kredyty, osiągnęła limit e-maili albo prepza tymczasowo wstrzymała zaproszenia, wszyscy członkowie firmy dostają powiadomienie z nazwą ATS. Kandydaci niezaproszeni z powodu braku kredytów są zapraszani automatycznie po doładowaniu, a oczekujących kandydatów z dowolnej oferty pracy można zaprosić ponownie jednym kliknięciem.
- **Slack, jeśli go używasz.** prepza może publikować powiadomienia, na przykład o kandydacie, który skończył, albo o kandydacie z ATS, którego nie udało się zaprosić, na wybranym przez Ciebie kanale Slack.
- **Twoja własna platforma.** Jeśli Twojego ATS nie ma na liście, [API](/api-docs) prepza pozwala zapraszać kandydatów za pomocą klucza API i odbierać podpisany webhook, gdy kandydat zaczyna lub kończy, gdy zaproszenie do niego nie dotrze lub wygaśnie, gdy kandydat zostanie usunięty i gdy rozmowa jest gotowa.
- **Dane przechowywane przez określony czas.** Kandydaci zapisani z ATS są usuwani po 365 dniach albo wcześniej, razem z ich rozmową lub firmą.

Niektóre ATS wymagają kroku po swojej stronie. Greenhouse, Teamtailor i Recruitee wymagają ręcznego dodania webhooka; okno Instrukcja w prepza pokazuje adres i miejsce, w które należy wkleić jego sekret. Webhooki Workable i Breezy HR prepza konfiguruje samodzielnie.

Płacisz za kandydata, bez subskrypcji: tylko za kandydatów, którzy odpowiedzą na co najmniej jedno pytanie — $5 za kandydata przy doładowaniu $50, $4 od doładowania $200, $3 od doładowania $600 i $2 od doładowania $1000. Ceny są tu w dolarach amerykańskich, a w Kanadzie, Australii, Izraelu, Polsce, Szwajcarii, Japonii, Korei Południowej, na Tajwanie, w Hongkongu, Tajlandii, Singapurze, Indiach, pozostałej części Europy i Wielkiej Brytanii w walucie lokalnej; VAT lub podatek od sprzedaży jest naliczany przy płatności. Połączenie ATS i tworzenie rozmów jest bezpłatne, a pierwszych 3 kandydatów Twojej pierwszej firmy jest za darmo. Zobacz [cennik](/pricing).

## Przeczytaj też

- [Jak przeprowadzić selekcję 100 kandydatów w jeden dzień](/guides/screen-100-applicants-in-a-day)
- [Testy umiejętności a selekcja CV](/guides/skills-tests-vs-cv-screening)
- [Testy rekrutacyjne: praktyczny poradnik](/pre-employment-testing)
