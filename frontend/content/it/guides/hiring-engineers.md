---
title: "Come assumere sviluppatori: un processo di selezione strutturato, dall'annuncio all'offerta"
seoTitle: "Come assumere sviluppatori: processo di selezione"
description: "Come assumere sviluppatori software, passo per passo: profilo del ruolo, screening, test tecnico, coding, system design, colloqui strutturati e offerta."
updated: "2026-10-29"
---

# Come assumere sviluppatori: un processo di selezione strutturato, dall'annuncio all'offerta

Assumere sviluppatori costa in un modo che è facile non vedere: la maggior parte del costo è il tempo dei tuoi stessi sviluppatori. Ogni ora che passano a fare un colloquio con qualcuno che non conosce lo stack è un'ora che non passano a costruire. Un buon processo mette prima i controlli economici e ad ampio raggio, e riserva quelli costosi e approfonditi alle poche persone che hanno buone probabilità di farcela.

Questa guida descrive quel processo passo per passo. Si basa sulla ricerca sulla selezione del personale dove i risultati sono chiari, e lo dice quando non lo sono.

## Il processo in sintesi

| Fase | Cosa verifica | Chi ci dedica tempo |
| --- | --- | --- |
| 1. Profilo del ruolo e annuncio di lavoro | Ciò di cui il ruolo ha davvero bisogno | Hiring manager, uno sviluppatore senior |
| 2. Screening dei CV o delle candidature | Solo i requisiti indispensabili | Recruiter o hiring manager |
| 3. Test di conoscenze | Cosa sa il candidato del tuo stack | Il candidato; tu leggi i risultati |
| 4. Esercizio a casa o live coding | Se sa scrivere codice funzionante | Uno o due sviluppatori |
| 5. System design (ruoli senior) | Come ragiona su sistemi più grandi | Uno sviluppatore senior |
| 6. Colloquio comportamentale strutturato | Come lavora con gli altri | Hiring manager, un collega |
| 7. Verifica delle referenze | Conferma di ciò che hai sentito | Hiring manager |
| 8. Decisione e offerta | Una decisione equa e documentata | Il team di selezione |

## Cosa dice la ricerca

Le grandi rassegne della ricerca sulla selezione del personale confrontano i metodi in base a quanto i loro risultati sono legati alla successiva performance lavorativa. La più recente tra quelle importanti, di Sackett, Zhang, Berry e Lievens (2022), ha rivisto al ribasso le stime precedenti e ha rilevato che i predittori più forti in media erano tutti misure specifiche per il lavoro ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). Le loro stime, su una scala in cui 0 indica nessuna relazione e 1 una relazione perfetta:

| Metodo | Validità stimata |
| --- | --- |
| Colloqui strutturati | .42 |
| Test di conoscenze professionali | .40 |
| Prove pratiche (work sample) | .33 |
| Colloqui non strutturati | .19 |
| Anni di esperienza lavorativa | .07 |

Ne seguono tre lezioni per la selezione di sviluppatori:

- **La struttura conta più del formato.** Lo stesso colloquio con domande prestabilite e una griglia di valutazione ha previsto molto meglio di una conversazione non strutturata.
- **Gli anni di esperienza, da soli, dicono poco.** "Cinque anni di Java" è un segnale debole rispetto a ciò che qualcuno sa e sa fare davvero.
- **Combina i metodi.** Nessun metodo da solo predice abbastanza bene da bastare.

Si tratta di medie su molti lavori e studi, non di garanzie per il tuo ruolo. Gli autori notano anche che i test di conoscenze e le prove pratiche sono adatti a ruoli in cui ci si aspetta che i candidati abbiano già formazione o esperienza. Questo vale per la maggior parte delle assunzioni di sviluppatori, ma non per un apprendistato.

## Passo 1: scrivi un profilo del ruolo e un annuncio chiari

Prima di pubblicare qualsiasi cosa, scrivi cosa farà la persona nei primi sei mesi e cosa deve sapere dal primo giorno. Sii specifico:

- **Deve sapere:** "Scrive e revisiona query PostgreSQL, compresi join e indici" si può verificare. "Ottime competenze sui database" no.
- **Imparerà sul lavoro:** i vostri strumenti interni, il vostro dominio, le parti dello stack che insegnerete voi.
- **Livello:** cosa distingue nel tuo team un mid-level da un senior, ad esempio essere responsabile di un servizio dall'inizio alla fine o guidare le decisioni di design.

Mettiti d'accordo su questo con tutti quelli coinvolti nell'assunzione. Poi scrivi l'annuncio a partire da lì. Un annuncio che corrisponde al lavoro reale attira le persone giuste e rende più facile impostare ogni passo successivo, perché ogni test e ogni colloquio si può ricondurre a esso.

Tieni corta la lista dei "requisiti preferenziali". Lunghi elenchi di requisiti scoraggiano persone qualificate che non spuntano ogni casella.

## Passo 2: usa lo screening dei CV solo per i requisiti indispensabili

Usa il CV o la candidatura per verifiche sì/no: permesso di lavoro, sede o fuso orario se il ruolo lo richiede, una lingua necessaria e qualsiasi requisito di cui il lavoro non può davvero fare a meno.

Non stilare classifiche in base al CV. Titoli di lavoro, nomi dei datori di lavoro e anni di esperienza sono predittori deboli, e i CV sono difficili da confrontare in modo equo: un CV forte può riflettere una buona scrittura tanto quanto un buon lavoro. Tratta il CV come un filtro per ciò che non si può testare, e porta chiunque lo superi al test di conoscenze.

## Passo 3: fai un breve test di conoscenze

È il passo che fa risparmiare più tempo ai tuoi sviluppatori. Prima che qualcuno passi un'ora in un colloquio dal vivo, verifica cosa sa ogni candidato del tuo stack.

Un buon test di conoscenze è:

- **Specifico per il ruolo:** verifica i linguaggi, i framework, i database e le pratiche del tuo profilo del ruolo, non nozioni generiche.
- **Breve:** pochi argomenti con circa 10 domande ciascuno, così anche i candidati forti che hanno altre offerte lo portano a termine.
- **Uguale per tutti:** stessi argomenti, stesso numero di domande e stessi limiti di tempo.

Qui entra in gioco testee. Trasforma la tua descrizione del ruolo in un colloquio di conoscenze a scelta multipla e a tempo. Rivedi gli argomenti proposti prima che venga scritta qualsiasi domanda, così il test copre il tuo stack e nient'altro. Per un ruolo tecnico, può includere:

- **Domande di lettura del codice:** un breve frammento di codice con domande su cosa stampa o restituisce, cosa fa, perché fallisce o quale modifica lo corregge.
- **SQL:** una piccola tabella e una query, con la domanda su quali righe vengono restituite.
- **Conoscenze di architettura e framework:** compromessi, come si comporta un framework, cosa va storto sotto carico.

Ogni candidato riceve il proprio set casuale di domande, con un conto alla rovescia su ognuna. Vedi una scheda di valutazione con ogni risposta e il tempo impiegato, più segnalazioni per risposte troppo rapide, uscite dalla pagina, tentativi di copia e andamenti insoliti nelle risposte e nei tempi. Una segnalazione è un motivo per guardare meglio, non la prova di qualcosa. Il report suggerisce anche domande a cui il candidato ha risposto correttamente, da approfondire nel colloquio successivo.

Cosa non fa testee: in testee i candidati non scrivono, non eseguono e non fanno debug del codice. Leggere codice e scriverlo sono competenze diverse, quindi il passo successivo resta importante. Vedi i [test di selezione per ruolo](/tests) per test pronti da cui partire.

## Passo 4: esercizio a casa o live coding

Ora verifica se i candidati sanno scrivere codice funzionante. È la fase per scrivere, eseguire e fare debug del codice, con un tuo esercizio o su una piattaforma per sviluppatori. Vedi le [alternative a HackerRank](/compare/hackerrank-alternatives) per capire come un test di conoscenze e una piattaforma di coding si integrano.

Due formati comuni:

- **Esercizio da svolgere a casa:** realistico e con poca pressione, ma occupa le serate dei candidati. Limitalo a poche ore al massimo, indica quanto dovrebbe durare e valutalo con una griglia scritta.
- **Live coding:** più breve e più difficile da far fare ad altri, ma più stressante. Lavora in coppia su un problema realistico, lascia che i candidati usino il linguaggio che conoscono meglio e giudica il loro ragionamento, non solo se arrivano alla fine.

In entrambi i casi, valuta in base a criteri concordati in anticipo: correttezza, leggibilità, test, gestione dei casi limite. Poiché il test di conoscenze ha già filtrato il gruppo, fai questo passo con poche persone invece che con tutti.

## Passo 5: system design per i ruoli senior

Per gli sviluppatori senior, aggiungi una discussione di design: "Come costruiresti un servizio che fa X?" Osserva come chiariscono i requisiti, come scelgono tra i compromessi e come individuano i punti di guasto. Raramente esiste un'unica risposta giusta, quindi una griglia di valutazione è indispensabile. Scrivi come appare una risposta debole, solida e forte prima del primo colloquio.

Saltalo per i ruoli junior, dove misura soprattutto la sicurezza di sé più che la competenza.

## Passo 6: colloqui comportamentali strutturati con griglie di valutazione

I colloqui strutturati erano il singolo predittore più forte in Sackett et al. (2022). Struttura significa:

- **Le stesse domande per ogni candidato,** legate al profilo del ruolo: "Raccontami di una volta in cui non eri d'accordo con una decisione di design. Cosa hai fatto?"
- **Una griglia di valutazione per ogni domanda,** con esempi di risposte deboli, solide e forti.
- **Punteggi indipendenti:** ogni intervistatore assegna il punteggio prima di confrontarsi con gli altri, così l'opinione più rumorosa non decide il risultato.

Usa questa fase per ciò che i test non possono mostrare: collaborazione, senso di responsabilità, gestione dei feedback, comunicazione con chi non è uno sviluppatore.

## Passo 7: verifica delle referenze

Le referenze possono confermare ciò che hai appreso e far emergere dubbi, ma trattale come un controllo finale, non come un test decisivo. Sackett et al. non hanno prodotto una stima di validità per la verifica delle referenze perché la ricerca disponibile era troppo scarsa, quindi ci sono poche prove di quanto bene predicano la performance. Se le fai, poni a ogni referente le stesse poche domande su comportamenti specifici.

## Passo 8: esperienza del candidato e tempi fino all'offerta

Gli sviluppatori forti hanno spesso diversi processi di selezione in corso contemporaneamente. Un processo lento o confuso li fa perdere.

- **Spiega subito ai candidati l'intero processo:** le fasi, quanto dura ciascuna e quando riceveranno una risposta.
- **Tienilo breve.** Programma le fasi finali ravvicinate e decidi poco dopo l'ultimo colloquio.
- **Rispetta il loro tempo.** Un breve test di conoscenze all'inizio significa che meno persone affrontano lunghi colloqui che difficilmente avrebbero superato.
- **Dai una risposta tempestiva a tutti,** comprese le persone che non fai avanzare.

## Equità in ogni fase

Un processo strutturato è anche più equo, ma solo se lo applichi in modo coerente:

- **Domande coerenti** in ogni fase, per ogni candidato allo stesso ruolo.
- **Griglie di valutazione scritte in anticipo,** così le persone vengono giudicate con gli stessi criteri.
- **Accomodamenti:** offri più tempo o un altro formato ai candidati che lo chiedono, ad esempio per una disabilità. In testee puoi dare a un candidato più tempo prima che inizi.
- **Monitora i risultati.** Metodi diversi mostrano divari di punteggio diversi tra i gruppi. Sackett et al. hanno rilevato differenze medie maggiori per i test di conoscenze professionali e le prove pratiche che per i colloqui strutturati, un motivo in più per combinare i metodi. Tieni d'occhio i tassi di superamento in ogni fase.
- **Decidono le persone.** Un punteggio supporta una decisione; non la prende. Guarda le risposte prima di scartare qualcuno.

Per le basi legali, compresi il regolamento UE sull'intelligenza artificiale (EU AI Act) e le norme statunitensi sui tassi di selezione, vedi [Test pre-assunzione](/pre-employment-testing).

## In sintesi

Metti prima i controlli ampi ed economici e per ultimi quelli approfonditi e costosi. Usa lo screening dei CV per i requisiti indispensabili, fai un breve test di conoscenze, poi spendi il tempo degli sviluppatori in coding, design e colloqui strutturati con i pochi rimasti. Valuta con griglie scritte in anticipo, e mantieni il processo rapido e chiaro.

## Fonti

- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection: Addressing systematic overcorrection for restriction of range. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Letture correlate

- [Test di selezione per ruolo](/tests)
- [Alternative a HackerRank](/compare/hackerrank-alternatives)
- [Guida ai test pre-assunzione](/pre-employment-testing)
- [Test attitudinali e di competenze o screening dei CV](/guides/skills-tests-vs-cv-screening)
- [Fare colloqui agli sviluppatori nell'era dell'IA](/guides/interviewing-in-the-age-of-ai)
