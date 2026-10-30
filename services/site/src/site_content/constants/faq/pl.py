# The FAQ in pl; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "Czym jest prepza?",
        "answer": "To rozmowa na czas stworzona z Twojego opisu stanowiska, dla dowolnej roli. Użyj jej do wstępnej selekcji kandydatów, zanim się z nimi spotkasz, albo jako etapu samej rekrutacji: tak czy inaczej zobaczysz, kto naprawdę zna się na rzeczy.",
    },
    {
        "key": "roles",
        "question": "Na jakie role mogę rekrutować?",
        "answer": "Na każdą rolę, w której liczy się wiedza: wsparcie klienta, sprzedaż, finanse, ochrona zdrowia, zawody techniczne, inżynieria, marketing i wiele innych. Jeśli potrafisz opisać stanowisko, prepza zbuduje do niego rozmowę.",
    },
    {
        "key": "hiring",
        "question": "Jak to działa?",
        "answer": "Wklej opis stanowiska na stronie głównej, podaj nazwę firmy i sprawdź tematy proponowane przez prepza. Potem zaproś kandydatów: wpisz ich adresy e-mail, wklej listę lub prześlij plik. Kandydaci, którzy po kilku dniach nie zaczęli, dostają jedno przypomnienie. Każdy kandydat dostaje własne pytania z limitem czasu na każde z nich, a Ty widzisz jego wynik i każdą odpowiedź, gdy tylko skończy.",
    },
    {
        "key": "link",
        "question": "Czy mogę umieścić rozmowę w ogłoszeniu o pracę?",
        "answer": "Tak. Włącz link do udostępnienia rozmowy na jej karcie ustawień i wklej go do ogłoszenia. Każdy, kto go otworzy, loguje się i bierze udział w rozmowie, a za każdą osobę płacisz jak za zaproszonego kandydata. Link wyłącza się, gdy oznaczysz w rozmowie, że ktoś został zatrudniony.",
    },
    {
        "key": "preview",
        "question": "Czy mogę wypróbować rozmowę, zanim kogoś zaproszę?",
        "answer": "Tak. Otwórz swoją rozmowę jako kandydat z jej strony, bezpłatnie: podglądy nie pojawiają się wśród Twoich kandydatów ani w statystykach pytań. Możesz też odbyć dowolną z darmowych próbnych rozmów.",
    },
    {
        "key": "open-to-offers",
        "question": "Czy firmy mogą mnie znaleźć dzięki moim ćwiczeniom?",
        "answer": "Tylko jeśli tego chcesz. Włącz „Rozważam oferty pracy” po rundzie ćwiczeń lub w Ustawieniach, podając adres swojego profilu LinkedIn. Firmy, które rekrutują przez prepza, zobaczą wtedy Twoje imię i nazwisko, profil LinkedIn i najnowszy wynik ćwiczeń z każdego tematu ich rozmów, który ćwiczyłeś, i mogą zaprosić Cię na rozmowę. prepza nie tworzy rankingu ani Cię nie poleca. Możesz to wyłączyć w każdej chwili w Ustawieniach, a wtedy od razu znikasz z list wszystkich firm; wyłącza się to też samo rok po tym, jak ostatnio to włączyłeś lub zapisałeś profil LinkedIn.",
    },
    {
        "key": "cheating",
        "question": "Czy kandydaci mogą korzystać z AI albo szukać odpowiedzi?",
        "answer": "Każdy kandydat dostaje własne losowe pytania we własnej kolejności, z [limitem czasu na każde pytanie](/guides/skills-test-timing-and-extra-time) pilnowanym przez nasz serwer, więc zostaje niewiele czasu na szukanie odpowiedzi czy pytanie AI. Wyniki pokazują też, kiedy kandydat opuścił stronę, skopiował tekst albo odpowiedział zbyt szybko, by przeczytać pytanie. Gdy kandydat skończy, jego strona wskazuje też wzorce odpowiedzi, jakie zwykle zostawia przekazywanie pytań AI, np. mniej więcej tyle samo czasu przy każdym pytaniu albo poprawne odpowiedzi na trudne pytania przy błędnych na łatwe, i podsuwa pytania, na które odpowiedział poprawnie, by dopytać o nie na rozmowie na żywo. Wzorzec to powód, by zapytać, a nie dowód. Przed startem każdy kandydat potwierdza też, że odpowie samodzielnie, bez narzędzi AI i pomocy innych osób, a jego wyniki to pokazują.",
    },
    {
        "key": "voice",
        "question": "Czy kandydaci mogą odpowiadać głosem?",
        "answer": "Tak, jeśli firma ustawi rozmowę w trybie głosowym (po angielsku, hiszpańsku, niemiecku, francusku, portugalsku lub włosku). Pytania są czytane na głos, a kandydaci odpowiadają na głos; to, co mówią, jest zamieniane na tekst i dopasowywane do odpowiedzi, którą potwierdzają, i nigdy nie jest zapisywane. Głosy nie są analizowane pod kątem tonu ani emocji, a kandydaci zawsze mogą zamiast tego dotknąć odpowiedzi.",
    },
    {
        "key": "cost",
        "question": "Ile to kosztuje?",
        "answer": "Generowanie rozmów jest darmowe. Każdy kandydat, który odpowie na co najmniej jedno pytanie, kosztuje {candidate} kredytów ({candidate_price}), a mniej z kredytami z większych doładowań, nawet {cheapest_price}. Twoja pierwsza firma dostaje {company} darmowych kredytów, co wystarczy na pierwszych {company_candidates} kandydatów. Wszystkie ceny są na [stronie cennika](/pricing).",
    },
    {
        "key": "charged",
        "question": "Kiedy płacę za kandydata?",
        "answer": "Jeśli odpowiedział na co najmniej jedno pytanie: gdy jego rozmowa się zakończy (sam ją zakończy albo skończy się czas, gdy go nie ma), albo gdy go wycofasz. Pytanie, którego czas minął bez wybranej odpowiedzi, się nie liczy. Jego kredyty są rezerwowane przy zaproszeniu i wracają, jeśli wycofasz go, zanim na cokolwiek odpowie, jeśli nigdy nie zacznie albo jeśli jego rozmowa zakończy się bez żadnej odpowiedzi.",
    },
    {
        "key": "compare_hiring",
        "question": "Jak cena wypada na tle innych narzędzi do oceny kandydatów?",
        "answer": "Wiele narzędzi do oceny kandydatów sprzedaje się w abonamencie miesięcznym lub rocznym, płatnym nawet wtedy, gdy nikogo nie testujesz. W prepza płacisz tylko za kandydatów: {candidate} kredytów ({candidate_price}) za kandydata, bez umowy, bez opłat za użytkowników i bez płacenia za wygenerowanie rozmowy. Firma, która zaprasza {example_candidates} kandydatów miesięcznie, płaci około {example_year_price} rocznie. Jeśli co miesiąc testujesz wielu kandydatów, abonament może wyjść taniej, więc porównaj to ze swoimi liczbami.",
    },
    {
        "key": "expire",
        "question": "Czy kredyty wygasają?",
        "answer": "Nie. Kredyty nigdy nie wygasają i nie ma płatnego abonamentu. Jeśli włączysz opcjonalne automatyczne doładowanie, Paddle zapisze Twoją kartę jako subskrypcję za {zero_price}; płacisz tylko za wykonane doładowania.",
    },
    {
        "key": "currency",
        "question": "W jakiej walucie płacę?",
        "answer": "Ceny są w walucie lokalnej w Kanadzie, Australii, Izraelu, Polsce, Szwajcarii, Japonii, Korei Południowej, na Tajwanie, w Hongkongu, Tajlandii, Singapurze i Indiach; w euro w pozostałych krajach UE oraz w Islandii, Liechtensteinie i Norwegii; w funtach w Wielkiej Brytanii; a gdzie indziej w dolarach amerykańskich. Twoje konto i każda firma zachowują walutę kraju, w którym zostały utworzone, niezależnie od tego, dokąd podróżujesz: swoją zmienisz w Ustawieniach, a walutę firmy obok jej przycisku „Doładuj” (właściciele i administratorzy). Doładowania firmy, także automatyczne, są zawsze pobierane w walucie firmy.",
    },
    {
        "key": "refunds",
        "question": "Czy mogę dostać zwrot?",
        "answer": "Tak, za kredyty kupione w ciągu ostatnich 14 dni i jeszcze niewydane: przez Paddle lub pisząc do nas. Darmowe kredyty, takie jak prezent powitalny, nie podlegają zwrotowi. Szczegóły są w [regulaminie](/terms).",
    },
    {
        "key": "scorecards",
        "question": "Co pokazują karty wyników?",
        "answer": "Każdą odpowiedź, czy była poprawna i ile trwała. Wynik to odsetek zdobytych punktów: każde pytanie jest warte jeden punkt, a pytanie wielokrotnego wyboru („zaznacz wszystkie poprawne”) daje jego część za każdą zaznaczoną poprawną odpowiedź i nic, jeśli zaznaczono błędną. Wyniki są oznaczone na zielono lub na czerwono względem progu zaliczenia ustawionego dla rozmowy. Karty wyników oznaczają też odpowiedzi zbyt szybkie, by przeczytać pytanie, opuszczenia strony i próby kopiowania.",
    },
    {
        "key": "reports",
        "question": "Czy mogę udostępnić wyniki menedżerowi rekrutującemu?",
        "answer": "Tak. Pobierz raport PDF dla jednego kandydata lub dla wszystkich kandydatów rozmowy, wyślij go e-mailem prosto z prepza albo prześlij krótkie podsumowanie przez WhatsApp, Telegram, Viber lub LINE.",
    },
    {
        "key": "action_log",
        "question": "Czy mogę zobaczyć, kto co zrobił w mojej firmie?",
        "answer": "Tak, jeśli jesteś właścicielem firmy. Zakładka Dziennik działań firmy pokazuje wszystko, co zrobili członkowie zespołu, od najnowszych: zapraszanie lub usuwanie kandydatów, przeglądanie wyników oraz zmiany w rozmowach, zespole, rozliczeniach i integracjach, wraz z tym, kto i kiedy to zrobił oraz czy zrobił to w jego imieniu asystent, aplikacja AI czy API. Możesz go filtrować według członka zespołu, rodzaju działania i dat. Działania są przechowywane przez 12 miesięcy. Działania klucza API są widoczne pod nazwą klucza. Właściciel może tam też pobrać eksport do audytu stronniczości: plik CSV z każdym kandydatem, który skończył, z jego wynikiem i informacją, czy zaliczył, na potrzeby niezależnego audytu stronniczości.",
    },
    {
        "key": "notes",
        "question": "Czy mój zespół może prowadzić notatki do rozmowy?",
        "answer": "Tak. Każda rozmowa ma zakładkę Notatki, w której Twój zespół pisze notatki zwykłym tekstem o rekrutacji, np. do kogo zadzwonić w następnej kolejności albo, w agencji rekrutacyjnej, dla którego klienta jest rozmowa. Każdy członek zespołu może pisać notatki, także obserwatorzy, i edytować swoje; usunąć notatkę mogą jej autor, właściciele i administratorzy. Właściciele i administratorzy mogą przypiąć jedną notatkę, która wtedy wyświetla się pod nazwą rozmowy. Kandydaci nigdy nie widzą notatek.",
    },
    {
        "key": "integrations",
        "question": "Czy prepza działa z moim ATS lub innymi narzędziami?",
        "answer": "Tak, bez dodatkowych opłat. Połącz Workable, Greenhouse, Teamtailor, Recruitee lub Breezy HR w zakładce Integracje swojej firmy: kandydaci, których przeniesiesz na etap, dostają rozmowę, a ich wyniki wracają do ATS ([jak połączyć testy umiejętności z ATS](/guides/ats-integration-skills-tests)). Slack może publikować powiadomienia firmy na kanale, a API pozwala Twojej własnej platformie tworzyć rozmowy, zapraszać kandydatów i zarządzać nimi oraz odbierać ich wyniki, a każdy klucz API może tylko to, co dla niego zaznaczysz; zobacz: [Dokumentacja API](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Czy mogę korzystać z prepza w Claude, ChatGPT lub we własnym agencie AI?",
        "answer": "Tak. Dodaj prepza do Claude lub ChatGPT jako konektor (kroki znajdziesz w zakładce Integracje swojej firmy) i zezwól na dostęp w prepza. Aplikacja działa wtedy w Twoim imieniu i z Twoimi uprawnieniami na Twoich firmach, rozmowach i wynikach kandydatów; większość aplikacji pyta Cię o zgodę, zanim cokolwiek zmieni. Konto lub firmę usuniesz tylko w prepza. To, co aplikacja odczyta, trafia do jej dostawcy na warunkach tej aplikacji. Możesz ją odłączyć w każdej chwili w tej samej zakładce. Połączyć można też inne aplikacje AI i agentów, których tworzysz samodzielnie: [zakładka MCP](/api-docs?tab=mcp) w dokumentacji dla deweloperów zawiera kroki i przykłady agentów, a agent na serwerze może się logować kluczem API z uprawnieniem do agentów AI. [Przewodnik po agentach AI, MCP i API](/guides/ai-agents-mcp-and-api) wyjaśnia, do czego służy każde z nich.",
    },
    {
        "key": "candidates",
        "question": "Co widzą kandydaci?",
        "answer": "Nazwę i logo Twojej firmy, w kolorach i czcionkach Twojej firmy (ustawionych na jej karcie Marka), przed startem informację, czego się spodziewać, a potem po jednym pytaniu z limitem czasu. Nigdy nie widzą swojego wyniku ani tego, czy odpowiedź była poprawna.",
    },
    {
        "key": "verified",
        "question": "Co oznacza znaczek weryfikacji?",
        "answer": "Że właściciel lub administrator firmy zalogował się służbowym e-mailem w domenie strony firmy, np. you@acme.com, a potem nasz zespół sprawdził firmę. Dodaj stronę przyciskiem Zweryfikuj w nagłówku firmy; darmowe usługi e-mail się nie liczą. Dopóki sprawdzenie trwa, Twój zespół widzi zegar obok nazwy, a zmiana nazwy firmy wysyła ją do ponownego sprawdzenia. Znaczek widać obok nazwy Twojej firmy, także w zaproszeniach.",
    },
    {
        "key": "languages",
        "question": "Jakie języki są obsługiwane?",
        "answer": "Liczba obsługiwanych języków: {count}, dla strony, rozmów i e-maili. Wybierz język, w którym ma być napisana rozmowa, niezależnie od języka opisu stanowiska.",
    },
    {
        "key": "privacy",
        "question": "Co dzieje się z opisami stanowisk i odpowiedziami?",
        "answer": "Opisy stanowisk służą do tworzenia rozmów Twojej firmy, a odpowiedzi kandydatów do ich oceny na potrzeby Twojej firmy. Pytania generowane przez prepza mogą być też ponownie wykorzystywane w rozmowach i rozmowach ćwiczeniowych innych firm, bez niczego, co identyfikuje Ciebie, Twoją firmę lub kogokolwiek innego; możesz wyłączyć z tego pytania danej rozmowy w jej ustawieniach. prepza wyodrębnia także z odpowiedzi na pytania ogólne, zanonimizowane wzorce jakości pytań, aby ulepszać sposób ich generowania. [Polityka prywatności](/privacy) wyjaśnia, co przechowujemy, jak długo i jakie prawa przysługują każdemu.",
    },
    {
        "key": "eu_ai_law",
        "question": "Czy w UE można legalnie używać AI do wstępnej selekcji kandydatów?",
        "answer": "Tak, na określonych zasadach. Zgodnie z unijnym AI Act narzędzia, które oceniają kandydatów, najpewniej należą do kategorii wysokiego ryzyka, z obowiązkami od 2 grudnia 2027, a RODO obowiązuje już teraz: decyzję o zatrudnieniu podejmuje człowiek, kandydaci wiedzą, że używana jest AI, a dokumentacja jest przechowywana. prepza działa właśnie tak: AI pisze pytania, osoby z Twojej firmy przeglądają wyniki i decydują, a kandydaci są informowani przed rozpoczęciem. To nie jest porada prawna; [Czy rekrutacja z AI jest legalna w UE?](/guides/is-ai-hiring-legal-in-the-eu) wyjaśnia zasady i terminy.",
    },
    {
        "key": "uk_us",
        "question": "Czy możemy używać prepza do kandydatów z Wielkiej Brytanii i USA?",
        "answer": "Tak. Umowa powierzenia przetwarzania danych obejmuje prawo Wielkiej Brytanii i USA, a instrukcje dla firm i wzory informacji dla kandydatów (z wersjami dla Nowego Jorku, Illinois i Kolorado) opisują, co musisz przekazać kandydatom. Do rekrutacji na stanowiska w Nowym Jorku używaj jej dopiero wtedy, gdy wykonasz to, czego wymaga od Ciebie Local Law 144: niezależny audyt pod kątem stronniczości w ciągu roku przed użyciem, opublikowanie jego podsumowania i powiadomienie kandydatów 10 dni roboczych wcześniej. Eksport do audytu stronniczości w Dzienniku działań daje Twojemu audytorowi wynik i rezultat każdego kandydata, który skończył, do połączenia z odpowiedziami, które Twoi kandydaci podali sami.",
    },
    {
        "key": "emails",
        "question": "Jakie e-maile wysyła prepza i jak je wyłączyć?",
        "answer": "E-maile serwisowe, takie jak zaproszenia, raporty, problemy z płatnością i zmiany naszego regulaminu, są wysyłane zawsze. Resztę, na przykład codzienne podsumowanie aktywności, przypomnienia i nowości o produkcie, wybierasz w Ustawieniach, w sekcji E-maile, albo wyłączasz linkiem „Wypisz się” w każdym e-mailu. Kandydaci mogą wyłączyć e-maile od Twojej firmy lub przypomnienia o danej rozmowie linkami w zaproszeniach i przypomnieniach. Aktualności prepza pojawiają się w Twoich powiadomieniach, pod dzwonkiem u góry; najważniejsze przychodzą też e-mailem jako nowości o produkcie, ale tylko wtedy, gdy to ustawienie jest włączone.",
    },
    {
        "key": "delete",
        "question": "Czy mogę usunąć konto?",
        "answer": "Tak, w Ustawieniach. Twoje konto i dane zostają usunięte, a wcześniej możesz pobrać ich kopię.",
    },
    {
        "key": "report",
        "question": "Jak zgłosić problem?",
        "answer": "Napisz do nas na [stronie kontaktowej](/contact) i wklej ID tego, czego dotyczy sprawa: „kopiuj id” jest pod nazwą firmy, rozmowy lub kandydata, a ID Twojego konta — w menu konta i w Ustawieniach. Dzięki ID od razu to znajdziemy.",
    },
]
